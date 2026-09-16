# Data quality — an audit against the cleaning literature

*Written 2026-09-13, findings F2 and F5 revised 2026-09-14. Read-only audit of
`data/processed/panel.parquet` (1,081,312 rows x 44 columns at the time of the
audit, **50 today**, 33,791 ZCTAs x 32 quarters), the L1 interim tables
(twelve then, fifteen now — `cbp_detail`, `zcta_geom` and `osm_landuse` were
built afterwards), the facility panel and the published cost ranking. Every
number below was computed against the files on disk. Nothing here was
estimated, rounded from memory, or taken from another document.*

*The six new columns are the quality flags F2 asked for. Where a finding has
been overtaken by later work it is marked REVISED and both states are kept,
because a finding that quietly becomes a compliment is not an audit.*

---

## 0. A note on where the citations come from

*This section was rewritten on 2026-09-13, later the same day, after the
papers were obtained and read. The original text said none of them was in
the repository and that every citation was from standard knowledge. That is
no longer true, and the change is not cosmetic — reading them corrected
three claims in this document, one of them a misclassification of our own
worst defect.*

The papers were downloaded by hand into `../Research/` and read in full,
cover to cover, including appendices and proofs. Section-by-section reading
notes, one file per paper, are in `docs/research/`:

```
  Rahm & Do (2000), "Data Cleaning: Problems and Current Approaches",
    IEEE Data Engineering Bulletin 23(4):3-13
      ../Research/TBDE2000.pdf         READ IN FULL, 11 pp.
      docs/research/NOTES_rahm_do_2000.md
      -> the taxonomy, verified against Figure 2 (rendered as an image,
         since it is not in the PDF text layer) and Tables 1-3.  Section 1
         of the scorecard below is the audit against it, and it has been
         CORRECTED in three places -- see the note under the scorecard.

  Fellegi & Holt (1976), "A Systematic Approach to Automatic Edit and
    Imputation", JASA 71(353):17-35
      ../Research/2285726.pdf          READ IN FULL, 20 pp. incl. Appendix
      docs/research/NOTES_fellegi_holt_1976.md
      -> the three criteria, the normal form of edits, implied edits, the
         complete set, Corollary 2's minimum-change result, and Section 7's
         a priori reliability weights.  Section 7 is the part that matters
         for F4 and it is the part we had not read.

  Winkler (1999), "State of Statistical Data Editing and Current Research
    Problems", US Census Bureau RR99-01
      ../Research/rr99-01.pdf          READ IN FULL, 10 pp.
      docs/research/NOTES_winkler_rr99_01.md
      -> how Fellegi-Holt is implemented in practice, with cost numbers,
         and macro / selective editing, which redesigns R9.
      -> NOT the same report as RR99-04.  RR99-04 is record linkage, is
         read, and is quoted at length in
         `src/siting_atlas/common/linkage.py`.  Section 6 of this document
         relies on that module's first-hand citations, unchanged.

  Van den Broeck, Argeseanu Cunningham, Eeckels & Herbst (2005), "Data
    Cleaning: Detecting, Diagnosing, and Editing Data Abnormalities",
    PLoS Medicine 2(10):e267
      ../Research/pmed.0020267.pdf     READ IN FULL, 5 pp.
      docs/research/NOTES_van_den_broeck_2005.md
      -> the three-stage REPEATING cycle, the four screening oddities, the
         four diagnoses, the three treatments, hard and soft cutoffs, and
         the definition of an erroneous inlier, which turns out to name
         F2 and F5 as one class.

  Two supporting surveys, also read in full:
      ../Research/2403.00526.pdf   The Five Facets of DQ Assessment, 20 pp.
      ../Research/1907.08138.pdf   A Survey of DQ Measurement and
                                   Monitoring Tools, 30 pp.
      docs/research/NOTES_five_facets_2024.md
      docs/research/NOTES_dq_tools_survey_2019.md

  Little & Rubin, "Statistical Analysis with Missing Data"
      -> read separately; see docs/research/NOTES_little_rubin_ch1_3.md.
         The MCAR / MAR / MNAR reasoning in F1 below is ours, applied to
         our own measurements.
```

Where this document says "the literature prescribes", it now means a
specific section of a specific paper that has been opened, and the section
number is given. Where a claim rests on a figure that is a raster image
rather than extractable text, the notes file says so. **No section number
is cited in this document that was not read.**

The *measurements* were always first-hand and are unchanged. What changed
is the frame, and it changed in ways that matter: see the correction note
immediately after the scorecard, and the revised F2, F4, R2 and R9.

Reproduction: the scripts that produced every figure were throwaway and
live in `/tmp`. They are short, and each section below names the columns
and the rule so the number can be recomputed from the parquet in a few
lines. Nothing in `src/` was modified.

---

## 1. Scorecard

Rahm & Do split cleaning problems along **three** axes, not two:
single-source versus multi-source (§2), schema-level versus instance-level
(§2), and — the axis this scorecard originally omitted — a four-level
**scope**: attribute, record, record type, source (§2.1). The scope column
is not decoration. It says which *kind of check* can find a class at all: a
record-type problem is invisible to any amount of per-attribute profiling,
which is exactly why `experiments/superseded-artefacts/panel_report.json` reports this data
as clean while three facility records contradict each other.

Figure 2 lists only two or three members per quadrant and ends each list
with an explicit "...". The full enumerations are Tables 1 and 2. What
follows is every class in Tables 1 and 2 plus the multi-source classes from
§2.2, against what this pipeline actually does. "Detect" means something in
the code notices; "treat" means something in the code acts.

```
SINGLE-SOURCE, SCHEMA LEVEL   (Rahm & Do Table 1 -- exactly four classes)
  class                    scope   detect treat  verdict / measured number
  ----------------------------------------------------------------------
  illegal values           attr    PART   PART   ACS negative sentinels are
                                                mapped to NULL (six codes,
                                                census_api.py:31). Nothing
                                                else is range-checked. 0
                                                negative values survive in
                                                the panel; 12 ZCTAs exceed
                                                100,000 people/sq mi and
                                                nobody looked.
  violated attribute deps  record  NO     NO    No cross-field edit exists
                                                anywhere. 353 ZCTAs have
                                                population > 0 and
                                                households = 0; 2 have
                                                establishments > 0 and
                                                employment = 0. Found by
                                                this audit, not by the code.
                                                NOTE: this class appears in
                                                BOTH Table 1 and Table 2.
                                                Ours is the instance-level
                                                form (Table 2's example is
                                                city="Redmond", zip=77777).
  uniqueness violations    rectype YES    n/a   assert_grain (panel.py:168)
                                                is a real contract and it
                                                holds: 1,081,312 rows =
                                                1,081,312 distinct
                                                (zcta, date_id) = 33,791x32
                                                exactly. Best single piece
                                                of validation in the repo.
  referential integrity    source  PART   PART  Joins are LEFT onto a dense
                                                gazetteer spine, so nothing
                                                fans out, but unmatched
                                                rates are never reported.
                                                CBP silently discards 4,074
                                                of 35,002 ZIPs (11.64%);
                                                540 of 928 CBSAs (58.19%)
                                                find no BLS OES match.

SINGLE-SOURCE, INSTANCE LEVEL   (Rahm & Do Table 2 -- nine classes)
  class                    scope   detect treat  verdict / measured number
  ----------------------------------------------------------------------
  MISSING VALUES           attr    YES    PART  Two distinct sub-problems,
   (incl. dummy values --                       and Rahm & Do put them in
    Table 2's example is                        ONE class.
    phone=9999-999999,
    "dummy values or null")
                                                (a) ordinary absence.
                                                Coverage is computed and
                                                written (panel.py:coverage,
                                                outputs/metrics/panel_report
                                                .json). One availability
                                                flag exists (rent_observed).
                                                No mechanism analysis; no
                                                imputation except two ad-hoc
                                                fallbacks.
                                                (b) DUMMY VALUES. REVISED
                                                2026-09-14. ACS top-codes
                                                are detected
                                                (census_api.flag_censoring)
                                                and the flag now REACHES
                                                the panel -- as do the
                                                bottom-codes $2,499 (23)
                                                and $9,999 (20), which
                                                nobody had looked for, and
                                                open_quarter_imputed. Seven
                                                flags, one declared
                                                registry
                                                (common/sentinels.py), one
                                                build gate
                                                (warehouse/flag_gate.py).
                                                But NO model, cost function
                                                or report conditions on any
                                                of them: 86 ZCTAs still
                                                carry income = $250,001 and
                                                83 carry home value =
                                                $2,000,001 as if they were
                                                measurements, 36 and 46 of
                                                those in the published cost
                                                ranking. Provenance, not
                                                repair. See F2 and F5.
  misspellings             attr    YES    YES   Jaro-Winkler + parsed
                                                address components,
                                                linkage.py. Thresholds
                                                measured off a real sweep,
                                                not borrowed. Genuinely good.
  cryptic values,          attr    PART   YES   Not previously scored. This
   abbreviations                               is what BL/BLVD.,
                                                GRANT LINE/GRANTLINE and
                                                SAINT HELENS/ST HELENS are
                                                in national_facilities.csv.
                                                linkage.py's address parser
                                                handles them correctly; it
                                                is simply never run over
                                                that file by the build.
  embedded values          attr    NO     NO    Not previously scored, and
   (Table 2: multiple                           previously MISNAMED -- this
    values in one field,                        class is several values
    name="J. Smith                              crammed into one free-form
    12.02.70 New York")                         field. No free-form fields
                                                survive to the panel. No
                                                evidence of any; no check.
  misfielded values        attr    NO     NO    Not checked. No evidence of
                                                any, but no evidence against.
  word transpositions      rectype NO     PART  Not previously scored.
                                                linkage.py's slot comparison
                                                is order-insensitive on
                                                parsed components, so it
                                                would survive them; nothing
                                                detects or reports them.
  duplicated records       rectype YES    NO    The matcher finds all three
                                                pairs in
                                                national_facilities.csv at
                                                score 1.000 with zero false
                                                positives — but it is never
                                                run over that file by the
                                                build. Diagnosis without
                                                treatment.
  contradicting records    rectype YES    NO    Rahm & Do keep this SEPARATE
                                                from duplication, and their
                                                example is two records for
                                                the same person with
                                                different birthdates. Ours
                                                is the same shape: the three
                                                pairs disagree about the
                                                OPENING DATE by 10, 6 and 3
                                                quarters. facilities.py:206
                                                silently takes min(open).
  wrong references         source  PART   NO    zcta/county_geoid/cbsa_code
                                                are all well-formed (0
                                                violations of the 5-digit
                                                rule). Whether a ZCTA is
                                                assigned to the RIGHT county
                                                is never checked. F11 is a
                                                real instance of this class.

MULTI-SOURCE, SCHEMA LEVEL
  naming conflicts               PART    NO     `metro` (Zillow), `cbsa_title`
                                                (OMB) and `metro_label`
                                                (project registry) are three
                                                different metro names in one
                                                frame; the first two disagree
                                                for 2,343 of the 8,349 ZCTAs
                                                where both exist (28.1%).
                                                `employment` (ZIP, CBP,
                                                median 574) and
                                                `metro_employment` (CBSA,
                                                OES, median 449,410) share a
                                                word and nothing else.
  structural conflicts           YES     YES    This is handled well. The
                                                Kimball layer (warehouse/
                                                schema.py) pins each source
                                                grain once, and optional.py
                                                refuses to join a source
                                                whose grain it cannot infer.

MULTI-SOURCE, INSTANCE LEVEL   (Figure 2 + the extra classes named only in
                                the prose of Rahm & Do §2.2)
  inconsistent aggregating       YES     NO     Known and commented, never
   (Fig. 2)                                     surfaced in the data. Five
                                                EJScreen columns are county
                                                means wearing ZCTA column
                                                names: 3,195 distinct values
                                                spread over 33,486 ZCTAs,
                                                ~10.5 ZCTAs per value. Wage
                                                columns are worse: 349
                                                distinct values over 18,475
                                                ZCTAs, 52.9 ZCTAs per value.
  inconsistent timing            PART    NO     The panel docstring is honest
   (Fig. 2)                                     that levels are pinned
                                                vintages. It does not say
                                                that a 2018Q1 row carries
                                                May-2025 wages and 2024
                                                EJScreen. 26 of 35 numeric
                                                columns are constant across
                                                all 32 quarters.
  different value                PART   YES   Named in §2.2, not Fig. 2.
   representations                              Gender-style encoding
                                                mismatches. Zero-padding
                                                discipline (see section 3)
                                                closes the one that bites in
                                                ZIP-level work.
  different interpretation       NO      NO     Named in §2.2, not in Fig. 2
   of values (§2.2's example                    -- "measurement units Dollar
    is "measurement units                       vs. Euro". Not previously
    Dollar vs. Euro")                           scored, and it is where the
                                                `employment` (ZIP, CBP,
                                                median 574) vs.
                                                `metro_employment` (CBSA,
                                                OES, median 449,410) trap
                                                actually lives -- same word,
                                                different unit of account.
  overlapping / contradicting    NO      NO     Two home-value series sit in
   (Fig. 2's box caption for                    the panel unreconciled. At
    this whole quadrant)                        2021Q3 the ZHVI/ACS ratio has
                                                p10 0.87 and p90 1.33; 17.2%
                                                of 24,675 ZCTAs differ by
                                                more than 25%.

NOT A RAHM & DO PROBLEM CLASS, BUT LOAD-BEARING HERE
  outlier detection              NO      NO     Zero screening of any kind,
                                                anywhere in src/. 28.36% of
                                                ZCTAs are robust-z outliers
                                                on household density and
                                                8.83% of the published cost
                                                ranking are robust-z outliers
                                                on cost_per_parcel.
                                                CORRECTION: this row used to
                                                say "not in Rahm & Do". That
                                                is half wrong. It is not a
                                                problem CLASS, but the
                                                detection method is in their
                                                Table 3 under data profiling
                                                -- "max, min should not be
                                                outside of permissible range"
                                                and "variance, deviation ...
                                                should not be higher than
                                                threshold". They prescribe a
                                                DECLARED plausibility band,
                                                not a distributional screen.
                                                See the revised F6 and R9.
  data profiling as a phase      NO      NO     Rahm & Do §3.1 and Table 3.
                                                Nothing in src/ derives
                                                value ranges, frequency
                                                distributions, patterns,
                                                constancy or cardinality as
                                                metadata. panel_report.json
                                                reports percent non-null and
                                                stops. The 2019 tools survey
                                                treats items like these as
                                                requirements 1-18 of 43; we
                                                have roughly 1-5.
  missingness mechanism          NO      NO     Never characterised. Section
                                                3 shows it is emphatically
                                                not MCAR.
  edit audit trail               PART    NO     Drops are logged to stderr
                                                and some are counted into
                                                report JSON. No edit is
                                                recorded in a form that could
                                                be reversed or replayed.
                                                Fellegi & Holt §6.1 items
                                                5-7 specify exactly three
                                                artefacts here and we have
                                                none of them; item 7, the
                                                uncorrected-vs-corrected
                                                cross-tab, we had never
                                                thought of.
  backflow of cleaned data       n/a     NO     Rahm & Do's fifth process
                                                phase (§3): write
                                                corrections back so they are
                                                not redone on the next
                                                extraction. We rebuild from
                                                raw every time, so an
                                                adjudicated facility date
                                                has nowhere to live except a
                                                code change. Relevant to R2.
```

Read that grid the way Van den Broeck's loop reads: **screening is decent,
diagnosis is patchy, treatment is almost absent, and the audit trail that
makes treatment reversible does not exist.** The project is good at
noticing and bad at acting, which is a much better failure than the reverse
but is not "best in class".

### 1.1 What reading the paper changed in this scorecard

Three corrections, recorded rather than quietly applied. Full detail in
`docs/research/NOTES_rahm_do_2000.md` and in
`docs/data/CLEANING_LITERATURE.md` §1.

**"Missing values" was filed under SINGLE-SOURCE, SCHEMA LEVEL. It is
instance level.** Rahm & Do Table 1 has exactly four schema-level classes —
illegal values, violated attribute dependencies, uniqueness violation,
referential integrity violation — and missing values is not one of them. It
is Table 2, instance level, attribute scope. Moved.

**The ACS top-code was filed under "embedded values". That is the wrong
class, and the error was load-bearing.** Rahm & Do's embedded values means
several distinct values crammed into one free-form field; their only
example is `name="J. Smith 12.02.70 New York"`. A sentinel standing in for
an unavailable measurement is their **missing values** class, whose
canonical example is `phone=9999-999999`, glossed "unavailable values
during data entry (dummy values or null)", and whose detection heuristic is
spelled out in their Table 3: "presence of default value may indicate real
value is missing".

Getting the class right merges two findings this document had treated as
unrelated. F2 (the ACS top-codes and bottom-codes) and F5
(`open_quarter.fillna(1)`) are **the same defect**: a dummy value occupying
a field that should say "unknown", surviving every range check because the
value is plausible. Van den Broeck names why they are invisible —
**erroneous inliers**, "data points generated by error but falling within
the expected range" — and predicts the outcome: "Erroneous inliers will
often escape detection." The current term of art, with a published
detector, is **hidden missing values** (Five Facets §3.3, §A.7). So the fix
is one declared per-source placeholder registry, not two unrelated
remediations. R1 and R3 have been revised accordingly.

**The scope axis was missing entirely, and four classes with it.** The
taxonomy is 2 x 2 x 4, not 2 x 2 (§2.1: "attribute (field), record, record
type and source"). Adding the scope column brought in four classes this
scorecard had never scored — cryptic values / abbreviations, embedded
values proper, word transpositions, and the multi-source
unit-interpretation class — and, more usefully, explained a puzzle. Our
duplicate and contradiction problems are *record-type* scope. Per-attribute
profiling cannot see them at any coverage level. That is why every metric
in `panel_report.json` is green while `national_facilities.csv` contains
three contradictions in the outcome variable.

---

## 2. Findings, worst first

### F1. The largest missingness is MNAR-shaped and is handled by dropping

`rent_index` is absent for 88.775% of panel rows. Partitioned by ZCTA:

```
  ZCTAs with at least one missing quarter   31,864 of 33,791   94.30%
  ZCTAs missing in ALL 32 quarters          27,199 of 33,791   80.49%
  ZCTAs absent from Zillow's file entirely  25,247 of 33,791   74.72%
```

Comparing the covariate distribution across the missing and present strata
(split on "any quarter missing", which is the 94.30% partition):

```
                                 present        missing      ratio
  median household density      1,555.6/sqmi    24.5/sqmi     63.6x
  median population density     3,920.4/sqmi    66.5/sqmi     59.0x
  median households                  16,166          869      18.6x
```

This independently reproduces the figure already in circulation
(1,556.8 vs 24.5). Using the stricter "missing in all 32 quarters"
partition gives 954.3 vs 16.9, a 56.4x gap — the conclusion does not depend
on which partition you pick.

**Mechanism.** Zillow publishes a rent index where it has enough listings,
and listing volume is a function of density and rental market thickness —
that is, of variables we observe. Formally that is MAR, not MNAR. But it is
MAR on a variable (`hh_density`) that is not in the covariate list of any
model here, and the conditional distribution is so extreme (64x) that
complete-case analysis on it is indistinguishable from selecting the
sample on the outcome. Little & Rubin's point stands either way: complete
case analysis is unbiased only under MCAR, and this is not remotely MCAR.

**Bias direction.** Any analysis that conditions on `rent_index` being
present is fitted on a sample whose median ZCTA is 64 times denser than the
population. Because both the cost model and the siting story are monotone
in density, every such estimate is biased toward the dense end and its
standard errors understate the extrapolation risk to the other 94%.

**What the pipeline does about it.** One good thing and one gap. The good
thing: `warehouse/panel.py` emits `rent_observed` as an explicit boolean
(verified: it equals `rent_index.notna()` exactly, True on 11.23% of rows),
with a comment that names the exact failure mode — a tree splitting on
"Zillow has no listing here" and learning it as a proxy for rural. That is
the availability-indicator approach the missing-data literature
recommends, implemented properly. The gap: nothing downstream conditions
on it, and no model imputes `rent_index`; the column is simply not used by
the cost model and the hazard model's covariate list is
`(households, median_household_income, establishments)`.

So the immediate damage is contained. The finding is that the largest
missingness in the dataset is unanalysed, and the one place its mechanism
was reasoned about is a code comment.

### F2. Censoring flags reach the panel and nothing reads them

**REVISED 2026-09-14, and the revision runs in the project's favour, so it is
stated precisely rather than generously.** This finding used to read
"censoring flags are computed and then thrown away", and the mechanism it
described — detection in `ingest/census_api.py`, loss somewhere in the L2
warehouse build, absence from the panel — **is no longer true.** What replaced
it is provenance, not repair. The flags now survive; no model, no cost
function and no report conditions on a single one of them. The censored values
are still being read as measurements by every consumer that reads them at all.

#### What was built

```
  common/sentinels.py       one declared registry, five Sentinel entries
                            across two sources. TOP / BOTTOM / ABSENT kinds.
                            detect() emits a boolean and NEVER edits a value,
                            so screening stays separate from editing.
  warehouse/flag_gate.py    an L3 build gate. Every flag in the registry, and
                            every column in any data/interim/*.parquet whose
                            name ends in _imputed / _topcoded / _bottomcoded /
                            _censored / _observed / _suppressed, must appear
                            as a column of the panel or the build raises.
                            No exemption list, deliberately.
  census_api.flag_censoring a thin alias over the registry, replacing the
                            inline loop this finding used to quote.
```

The panel has **50 columns, seven of them quality flags** — it had 44 and one
when this finding was written. Verified against `data/processed/panel.parquet`
(1,081,312 rows, 33,791 distinct ZCTAs):

```
  flag                                    distinct ZCTAs   panel rows
  -------------------------------------   --------------   ----------
  median_home_value_topcoded                          83        2,656
  median_home_value_bottomcoded                       20          640
  median_household_income_topcoded                    86        2,752
  median_household_income_bottomcoded                 23          736
  rent_observed                                    1,928      121,379
  wage_suppressed                                      0            0
  open_quarter_imputed                               433       13,856
```

Three things in that table are worth reading twice. The ACS counts are
**exactly** the ones this finding measured in the interim parquet before the
gate existed, so nothing was lost in transit. **The bottom-codes, which this
finding reported as never having been looked for, are now detected** — 20 and
23 ZCTAs. And `wage_suppressed` is carried but is true nowhere, which is a
flag doing its job: it says the BLS withheld nothing in this extract, which is
a different statement from not having checked.

#### What was not built, and it is the half that mattered

**No model, no cost function and no report conditions on any of the seven.**
Verified by grep over `cost/`, `models/`, `optimize/`, `viz/`, `app/`,
`agent/` and `report/`: not one of the seven flag names appears in any of
them. Every reference lives in `warehouse/` or `ingest/` — that is, in the
code that *creates and plumbs* the flags, not in code that *acts* on them.
The single apparent exception, `open_quarter_imputed` at
`warehouse/facilities.py:188`, is inside a log line; it changes the message
printed, not the target column.

So the consequence this finding measured is unchanged in every particular:

Consequences, measured, and **still live**:

```
                                 nationally   in the published 2,333-ZCTA
                                              cost ranking for 2023Q4
  income top-coded  $250,001            86                             36
  income bottom-coded $2,499            23                              0
  home value top $2,000,001             83                             46
  home value bottom $9,999              20                              0
```

The bottom-codes were an additional finding: nobody had looked for them. The
ACS bottom-codes median household income at $2,499 and median home value
at $9,999, and 23 and 20 ZCTAs sit exactly on those values. They are
lower/upper bounds, not measurements. They are **now detected and carried**,
and they are **still being read as measurements**, because detection is where
the work stopped.

Thirty-six of the 2,333 ZCTAs in the headline cost ranking (1.5%) have
their income — which drives `daily_parcels` through the income elasticity
at `cost/daganzo.py:91-94` — set from a censoring code. These are Palo
Alto-class ZCTAs, so the bias runs one way: their parcel demand, and
therefore their cost advantage, is understated.

**Classification, corrected 2026-09-13 after reading the papers.** This
paragraph used to say "This is Rahm & Do's 'embedded values' class". It is
not. Embedded values means several values crammed into one free-form field
(`name="J. Smith 12.02.70 New York"`). This is Rahm & Do's **missing
values** class — Table 2, attribute scope, instance level — whose canonical
example is `phone=9999-999999`, glossed "unavailable values during data
entry (dummy values or null)". Their Table 3 even gives the detection rule
we never ran: *"presence of default value may indicate real value is
missing"*.

Two consequences of getting the class right.

First, **F2 and F5 are one defect, not two.** `open_quarter.fillna(1)` is
the same thing: a dummy value in a field that should say "unknown". Van den
Broeck names the mechanism that hides both — they are **erroneous inliers**,
"data points generated by error but falling within the expected range", and
he predicts what happened: "Erroneous inliers will often escape detection."
$250,001 is a plausible income. Q1 is a plausible quarter. No range check
will ever find either. The current literature calls the class **hidden
missing values** and has a detector for it (Five Facets §3.3 and §A.7,
citing FAHES).

Second, **the fix is a registry, not four booleans.** Van den Broeck's
Diagnostic Phase gives the instruction in one line — *"Substitute code
values for missing data should be corrected before analysis"* — and Five
Facets §3.3 says where the knowledge lives: "Placeholders can differ for
each data source or be domain-specific, which is why strict documentation
is important." So: declare the sentinel set per source in one place;
convert to NULL plus an explicit censoring indicator at ingest; carry the
indicator to the panel; and treat the censored state as a *code* rather
than an absence, so that an edit can refer to it (Fellegi & Holt §2 note
3(a)). The bottom-codes fall out of the same registry for free. R1 has been
revised.

**Four of those five clauses are now done.** The registry exists
(`common/sentinels.py`); it is applied at ingest; the indicator is carried to
the panel and a gate enforces it; the bottom-codes did fall out for free. The
one not done is the one Van den Broeck's sentence is actually about —
*"corrected before analysis"*. The value is deliberately left exactly as the
publisher wrote it, on the correct principle that screening is not editing,
and no consumer has since been taught to treat $250,001 as a bound. The
registry docstring says as much in its own words: "this function only makes
the choice available".

So the finding survives with its scope reduced and its edge intact. **It is no
longer the clearest case in the repo of detection without treatment; it is now
the clearest case of provenance without treatment**, which is one step better
and two steps short. The number in the headline cost ranking has not moved,
and R1's estimate of what fixing it would affect — 36 ZCTAs on income, 46 on
home value — is unchanged.

### F3. There is no formal edit system, and the implicit constraints are violated

Fellegi & Holt's contribution is that edits should be *declared as
constraints over fields*, checked as a set, and used to localise error —
rather than implemented as a scatter of ad-hoc filters at the point of use.
This project has the scatter and none of the system.

Two clarifications now that the papers have been read. Fellegi & Holt's
**formal definition of an edit** (§2, eq. 2.2-2.3) is a subset of the code
space "declared a set of unacceptable code combinations", and every edit
reduces to the *normal form*: "a specified combination of code values is
not permissible." And Winkler RR99-01 §1 states the objection to what we do
instead more precisely than "it is untidy" — the problem with if-then-else
rules is not that they give wrong answers but that they are hard to make
logically complete, hard to code correctly, and expensive to *change*,
because "If there are slight changes in the survey form and edit rules,
then subsets of thousands of lines of code may need to be rewritten and
debugged."

Winkler also supplies a caveat we should apply to our own list before
enforcing any of it. On an edit flagging married under-16s: "Application of
this edit is necessarily a compromise. In a few situations, changing the
marital status of a person who has age less than 16 to unmarried might
induce an error. In most situations, the change would be a correction."
**An edit is a bet, not a fact.** Our `population > 0 ==> households > 0`
fires on 353 ZCTAs, most of which are almost certainly group quarters —
correct records that an enforced edit would damage.

Here is what a minimal edit set would catch, tested by hand for this audit:

```
  edit                                            violations   of
  ------------------------------------------------------------------
  households <= population                                 0   33,791
  owner_occupied + renter_occupied <= households           0   33,791
  owner_occupied + renter_occupied == households          19   33,791
  vehicle_availability_total == households                19   33,791
  bachelors_degree <= population                           0   33,791
  in_labor_force <= population                             0   33,791
  land_area_sqmi > 0                                       0   33,791
  latitude in [-90, 90], longitude in [-180, 180]          0   33,791
  population > 0  ==>  households > 0                    353   33,791
  households > 0  ==>  population > 0                      0   33,791
  population / households in [1, 10]                     137   33,791
  establishments > 0 ==> employment > 0                    2   33,791
  annual_payroll > 0 ==> employment > 0                    2   33,791
  implied pay/employee in [5k, 500k]                       6   30,928
  low_income_pct, people_of_colour_pct in [0, 1]           0    *
  median_age in (0, 100]                                   0   33,791
  zcta matches ^[0-9]{5}$                                  0   33,791
  county_geoid matches ^[0-9]{5}$                          0   33,791
  cbsa_code matches ^[0-9]{5}$ when present                0   33,791
  date_id == concat(year, 'Q', quarter)                    0    all rows
  (zcta, cbsa_code) stable across 32 quarters              0   33,791
  facility open_q_index <= close_q_index                   0   UNTESTABLE
```

The good news first: most of the edits pass, and the assignment-stability
edits pass completely — no ZCTA changes county, state, CBSA, land area or
coordinates across the 32 quarters, which is what you want from a pinned
2020 geography. The 19 violations of the household identities are the same
19 ZCTAs that are in the 2020 gazetteer but absent from ACS 2023 (they have
NULL on every ACS field, so the identity is vacuously unequal rather than
contradicted). That is a false positive of the edit as written, and
illustrates why Fellegi & Holt insist edits be declared and reasoned about
rather than improvised — an edit that fires on missingness is a broken edit.

**And Fellegi & Holt supply the fix, in two lines.** §2 note 6:

> "We accept a convention that whenever one of the fields of a record
> contains an invalid entry (i.e., one which is not among the set of
> possible values), we consider the record as failing all edits which that
> field enters explicitly."

Combined with note 3(a) — reserve one extra code per field representing
"all the invalid codes of Field i", and map invalid entries to it at load
— the 19 ZCTAs stop being an arithmetic accident and become a declared,
countable state. "Fails the ACS presence edit" is a different finding from
"fails the household identity", and only the first one is true. §5.1 shows
the same trick in their bit-matrix representation: "All we need do is
expand the code set for every field by the inclusion of an extra code
labeled 'Invalid'."

The same convention resolves `enabled.fillna(False)` at
`facilities.py:215`. Note 6 continues: "The code value 'blank' may or may
not be among the set of possible (i.e., permissible) values of a field."
"Not covered by any known catchment" is a permissible blank; "known not to
be served" is a value. Collapsing them is precisely the error the
convention exists to prevent.

The real violations:

- **353 ZCTAs report population > 0 and households = 0.** ACS table B11001
  counts households; B01003 counts people. A place with people and no
  households is either a group-quarters ZCTA (a prison, a campus, a
  military base) or an error. The code never distinguishes them. It matters
  because `cost/runner.py:57` drops on `households > 0`, so all 353 leave
  the cost model without anyone deciding whether a 3,000-inmate facility
  has delivery demand.
- **137 ZCTAs have more than 10 people per household.** Same population,
  same cause. The maximum is unbounded because the denominator can be 1.
- **2 ZCTAs have establishments and payroll but zero employment**, and
  6 have implied annual pay per employee outside $5k-$500k. CBP suppresses
  employment counts in small cells and publishes an establishment count
  anyway; the suppression is not flagged in `data/interim/cbp.parquet`.

**`open_date <= close_date` is untestable.** `close_year` is NULL for all
104 rows of `national_facilities.csv` and for 42 of the 43 rows of
`facilities.csv`. `warehouse/facilities.py:120` handles the absence
correctly (`close_q_index = inf`), so the edit would pass — but it would
pass vacuously, and a green edit that can never fail is not evidence.

### F4. Three *contradicting* facility records, contradicting in the outcome

`docs/data/FACILITY_PANEL_PROVENANCE.md` §12.6 already records "104 rows
describing 101 buildings". That
undersells it. Running `common/linkage.py` over `national_facilities.csv`
for this audit — 5 candidate pairs generated by the two blocking keys —
returns:

```
  match  NAT-0011 / NAT-0012   score 1.000   street exact, geo agrees
    '2815 W EL SEGUNDO BL'     HAWTHORNE CA 90250   open 2020 Q2
    '2815 W. EL SEGUNDO BLVD.' HOLLYGLEN CA 90250   open 2017 Q4
  match  NAT-0025 / NAT-0026   score 1.000   street exact, geo agrees
    '1500 EAST GRANT LINE ROAD' TRACY CA 95304      open 2025 Q1
    '1500 E GRANTLINE RD'       TRACY CA 95304      open 2026 Q3
  match  NAT-0078 / NAT-0079   score 1.000   street exact, geo agrees
    '3610 NW SAINT HELENS RD'   PORTLAND OR 97210   open 2017 Q4
    '3610 NW ST HELENS RD'      PORTLAND OR 97210   open 2018 Q3
  nonmatch x2
```

Three matches at score 1.000, two correct non-matches, zero false
positives. The matcher works. But:

1. **The paired rows disagree about the opening date by 10, 6 and 3
   quarters.** That is Rahm & Do's "contradicting records" — the same
   real-world entity with conflicting attribute values — and the
   conflicting attribute is the one the entire siting model is trying to
   explain. A duplicate row you can delete. A contradicted date you have to
   *adjudicate*, and nobody has.
2. **`enabled_flags` (facilities.py:206-210) resolves the contradiction
   silently and always in the same direction**: it takes `min(open_q_index)`
   across every facility whose catchment covers a ZCTA, so the earlier of
   the two dates always wins. For the Hawthorne pair that switches a
   fifteen-mile Los Angeles catchment on ten quarters early.
3. **Nothing in the build runs the matcher over this file.**
   `tests/unit/test_linkage.py:212` runs it over `facilities.csv` (the
   43-row pilot file, which is clean), and the docstring at line 204 states
   that the same check over `national_facilities.csv` finds three pairs.
   The test that would fail is not written.

The three pairs differ only by abbreviation — `BL`/`BLVD.`,
`GRANT LINE`/`GRANTLINE`, `SAINT HELENS`/`ST HELENS`. That is Rahm & Do's
*cryptic values, abbreviations* class (Table 2), not misspellings proper;
`linkage.py` handles it perfectly, and the solution is not connected to the
data.

#### What Fellegi-Holt actually prescribes here

Worked out properly, because `min()` needs replacing and another agent may
implement this. Full derivation in
`docs/research/NOTES_fellegi_holt_1976.md` §5.1 and
`docs/data/CLEANING_LITERATURE.md` §3.3.

Note first that identity is *not* the question. `linkage.py` settles that at
score 1.000 with zero false positives, which is Fellegi-**Sunter** doing its
job. What follows is the next problem, and it is Fellegi-**Holt**'s.

**1. Declare the edit.** In normal form (§2, eq. 2.7), over a merged entity
carrying both sources' date fields:

```
  E_date :  (link_score >= STREET_MATCH)
            INTERSECT (open_q_index_A != open_q_index_B)  =  F
```

That is a legitimate Type B edit in Fellegi & Holt's §1 sense — "the
checking of entries in certain predetermined combinations of fields to
ascertain whether the entries are consistent with one another". It is
currently declared nowhere.

**2. Error-localise.** Build the failed edit matrix (§5.4): rows are failed
edits, columns are fields, a cell is 1 where the field enters the edit
explicitly. For each pair the two records agree on street (after
standardisation), city, state, ZIP and geography and disagree only on the
date, so `E_date` is the only failed row and the minimum cover is the
single column `open_q_index`. **Corollary 2 therefore says: change the date
field and change nothing else.** That is already more than `min()` gives
us, because `min()` records neither that a field was changed nor which one,
and a reader of the panel cannot distinguish an adjudicated date from a
reported one.

**3. Recognise what Corollary 2 does NOT give you.** It asserts that
satisfying *values exist*; it does not choose one. §4's imputation machinery
derives the admissible set from the edits (eq. 4.2), and here that set is
uninformative — any value with `open_q_index_A == open_q_index_B` passes,
so 2020Q2 and 2017Q4 are equally admissible. **The edits do not pin down
the date.** R2 as originally written said "the minimum change is one date
per pair", which slides from *which field* to *which value*. Corrected
below.

**4. §7 supplies the missing rule: a priori reliability weights.**

> "It often happens that one has an a priori belief that some fields are
> less likely to be in error than others. If one field is the product of a
> complicated coding operation and the other is a self-coded response,
> then, intuitively, one is inclined to believe that the simple self-coded
> response is more likely to be error-free. ... where there is more than one
> minimal set of fields, an a priori weight of the reliability of each
> field could easily be used to select among the minimal sets of fields the
> one to be imputed. For example, we could simply take the set with the
> lowest product of a priori weights." (Fellegi & Holt §7)

For us the weight attaches to the **provenance of each date**, and Fellegi
& Holt's coded-versus-self-reported distinction maps onto ours directly: an
OSHA inspection date is a derived artefact of a regulatory process with a
known, variable lag (`docs/METHODS_RESEARCH.md` §15.1 records externally
verified lags of 4, 13, 57, 69 and 345 months); a permit or press record is closer to a
direct report. Declare the ranking once, in
`docs/data/FACILITY_PANEL_PROVENANCE.md`, and apply it mechanically.

§7's less subjective alternative — "determine for each field the proportion
of edits entered by the fields which are failed" — has no signal at three
pairs and we should not pretend otherwise.

**5. Where the provenances rank equal, stop guessing.** §1, option 2: "one
should, whenever possible, avoid 'manufacturing' data instead of collecting
it." Three permit lookups. R2's *action* was right all along; only its
justification was wrong.

**6. Log it.** §6.1 items 5-7: per-record log of edits failed, per-edit log
of records failing, and the uncorrected data preserved and cross-tabulated
against the corrected.

**Why `min()` is specifically wrong**, in the paper's own terms — three
separate objections, worth keeping separate:

1. It is an imputation rule *specified independently of the edits*, which
   is exactly what Criterion 2 exists to abolish ("It should not be
   necessary to specify imputation rules; they should derive automatically
   from the edit rules") and what §1 blames for corrections whose "net
   impact on the data is unforeseeable".
2. It is **directional**. `min()` always resolves toward the earlier date,
   so it is a biased estimator of the opening quarter — biased early, by
   construction, on every conflicting pair. At a median 58 ZIPs per station
   that is roughly 170 ZCTA-quarters of the target variable set by a
   systematic bias rather than by an error.
3. It therefore also violates Criterion 3, which asks that imputation
   "maintain, as far as possible, the marginal and even preferably the
   joint frequency distributions of the variables". Systematically taking
   the minimum shifts the whole opening-date distribution earlier.

One encouraging note, from Van den Broeck's small-study discussion: with
104 national rows "the diagnostic phase can be cheaper and the whole
procedure more complete". We can adjudicate *all* of them, which is not
true of 33,791 ZCTAs. And Box 2's third screening method — "Browsing of
data tables after sorting" — would have surfaced these three pairs in about
a minute, where statistical screening on 43 rows "may become less valid
with smaller samples".

### F5. An imputation default has put a visible artefact in the outcome variable

`warehouse/facility_load.py:107-108` (the code moved out of
`warehouse/facilities.py` after this finding was written):

```python
    frame["open_q_index"] = (frame["open_year"] * 4
                             + frame["open_quarter"].fillna(1) - 1)
```

The comment defends it well — "placing the event at the start of the year
is a stated convention; dropping the row would silently shrink the event
count, which is worse" — and the reasoning is right. The problem is the
magnitude, which the comment does not give:

```
  facilities.csv rows                                     43
  rows with no open_quarter, defaulted to Q1              19   (44.2%)
  share of fitted events falling in Q1                 35.47%
  share expected if quarters were uniform              25.00%
```

The 35.47% is not my number — it is already in
`experiments/hazard-model/artefacts/hazard_report.json` under `event_timing/share_in_q1`,
which means the project *measures* the artefact and does not act on it.
Ten percentage points of spurious Q1 seasonality has been injected into the
target variable of a model that fits a four-knot spline in calendar time.

**Placed against the literature, 2026-09-13.** Three things sharpen.

*This is the same class as F2.* Q1 is a plausible quarter; the value is a
dummy standing in for an unknown. Rahm & Do's **missing values** class
(`phone=9999-999999`), Van den Broeck's **erroneous inlier**, Five Facets'
**hidden missing value**. One registry fixes both. See §1.1 above.

*The 35.47% is a screening signal that never got a diagnosis.* Van den
Broeck's third screening oddity is "strange patterns in (joint)
distributions". The project screened, found one, wrote it to a report, and
stopped. Under the framework a suspect without a verdict is an unfinished
job, not a finished one — and the whole point of separating the stages is
that screening produces suspects, not conclusions.

*The reversibility failure has a concrete cost, stated in the paper's own
terms.* Van den Broeck's first diagnostic procedure is "to go to previous
stages of the data flow to see whether a value is consistently the same.
**This requires access to well-archived and documented data with
justifications for any changes made at any stage.**" That sentence described
the state of the code when it was written and no longer does.

**REVISED 2026-09-14.** The NULL is no longer destroyed. `open_quarter` keeps
it, `flag_sentinels(frame, "facility_panel")` runs immediately before the
`fillna(1)`, and `open_quarter_imputed` travels with the date through
`warehouse/facilities.py` into the panel — true on 433 distinct ZCTAs and
13,856 panel rows. The reversibility failure is repaired; recovering the
pre-default state is reading one column.

What is *not* repaired is the consequence. `open_q_index` still carries Q1,
and the 35.47% Q1 share is unchanged, because no model conditions on the flag
— `open_quarter_imputed` appears nowhere in `models/`, and its one use in
`warehouse/facilities.py:188` is a log line. The correct statement is now: a
model **can** condition on "this date is a convention" and none does. Same
class as F2, same half-closure.

The treatment the paper would ask for is cheaper than choosing a better
default: retain the flag and the original, and then run the model with and
without the 19 imputed-quarter facilities — "separate analyses with and
without remaining outliers and/or with and without imputation" — and
publish the difference.

Two related facts from the same file:

- **All 43 facility coordinates are NULL** and all 43 are filled from the
  ZCTA centroid (`facilities.py:144-149`). The fallback is reasonable and
  logged. But every catchment in the project is a fifteen-mile circle drawn
  around a centroid, not a building, and that geometry is what produces the
  "104 decisions plus a circle" problem already diagnosed in
  METHODS_RESEARCH.md §14.2.
- **`facilities.py:215` does `enabled.fillna(False)`.** The panel's
  `enabled` column is `bool` with zero NULLs and 27,914 True. The
  `panel.py` module docstring still claims the target is "present, all
  NULL, and typed" — that is now stale. "Not covered by any known
  catchment" and "known not to be served" have been collapsed into the same
  `False`, which is exactly the encoding the docstring was written to
  prevent.

### F6. No outlier detection exists, and the extremes are unclassified

Nothing in `src/` screens for outliers. Not a z-score, not an IQR fence,
not a winsorisation, not a plausibility band. Running a robust screen
(modified z on the median/MAD, flagging |z| > 3.5; and a 3x IQR fence) for
this audit:

```
  column                        n      |rz|>3.5          3xIQR      max
  ----------------------------------------------------------------------
  household density         33,772   9,578 (28.36%)  4,277 (12.66%)  79,087
  annual_payroll            30,928   8,688 (28.09%)  2,569 ( 8.31%)  30.7bn
  employment                30,928   8,605 (27.82%)  2,039 ( 6.59%) 204,898
  establishments            30,928   7,518 (24.31%)  1,266 ( 4.09%)   6,396
  households                33,772   7,756 (22.97%)    790 ( 2.34%)  42,673
  population                33,772   7,702 (22.81%)    907 ( 2.69%) 137,213
  traffic_proximity      1,071,552 224,224 (20.93%) 52,960 ( 4.94%)   14.5m
  land_area_sqmi            33,791   3,069 ( 9.08%)  1,430 ( 4.23%)  13,678
  median_home_value         30,311   1,904 ( 6.28%)    813 ( 2.68%)   2.0m
  rent_index               121,379   2,447 ( 2.02%)    712 ( 0.59%)  68,623
  diesel_usd_gal         1,076,544       0 ( 0.00%)      0 ( 0.00%)    6.12
  ---- published cost ranking, 2023Q4 baseline, n=2,333 ----
  cost_per_parcel            2,333     206 ( 8.83%)    146 ( 6.26%)    6.41
  local_miles_per_stop       2,333     367 (15.73%)    206 ( 8.83%)    3.53
  linehaul_miles             2,333     164 ( 7.03%)    100 ( 4.29%)   86.03
  daily_parcels              2,333       9 ( 0.39%)      0 ( 0.00%)  25,984
```

**The rates are high because the distributions are heavy-tailed by nature,
not because the data is dirty.** That distinction is the whole point, and
it is the reason a naive outlier filter here would be actively harmful.
Worked through:

- *Extreme and correct.* The twelve ZCTAs above 100,000 people/sq mi are
  10069, 11109, 10028, 10162 and 10128 — Manhattan and Long Island City.
  ZCTA 10069 is 6,669 people on 0.041 sq mi = 162,659/sq mi. That is
  arithmetically right and substantively right. A 3-sigma filter deletes
  Manhattan, which for a delivery-siting project deletes the answer.
- *Extreme and correct.* The three ZCTAs above 10,000 sq mi are Alaskan and
  Nevadan; max 13,678 sq mi.
- *Extreme and correct.* `cost_per_parcel` = $6.41 at ZCTA 83650 (Boise,
  550 people, 64 stops/day, 61 miles of line haul). The model is doing what
  it should.
- *Extreme and probably an artefact.* `rent_index` = $68,623/month at ZCTA
  11976 (Water Mill, NY) and $41,430 at 11963 (Sag Harbor). Zillow's ZORI
  in Hamptons ZIPs is contaminated by summer-season whole-house lettings;
  126 panel rows exceed $10,000/month across 8 ZCTAs. Nothing flags them.
- *Extreme and structurally wrong.* `permits_yoy_pct` hits +5,900% and
  exactly -100% on 6,232 rows (1.04%). The -100% rows are a county going to
  zero permits; the +5,900% rows are a county going from one unit to sixty.
  Both are arithmetically defensible ratios on tiny denominators and both
  are useless as features. There is no denominator floor anywhere.
- *Extreme and a units question nobody has answered.* `traffic_proximity`
  runs to 14,529,474 and is identical to seven significant figures across
  every ZCTA in Suffolk County, MA. See F7 — it is a county value.

So: the honest verdict is not "we have 28% outliers". It is "**we have
never once looked, so we do not know which of our extremes are Manhattan
and which are Water Mill**". Van den Broeck's screening stage does not
exist.

#### What the literature actually prescribes here — and it is not a z-score

Reading the papers changed this finding more than any other, because two of
them point away from the screen we were about to build.

**Rahm & Do do not prescribe a distributional screen.** Their detection
rule for illegal values (Table 3, under data profiling) is metadata-driven:
"max, min should not be outside of permissible range" and "variance,
deviation of statistical values should not be higher than threshold". That
is a **declared plausibility band per column**. A robust-z on household
density contains no notion of a permissible range and therefore cannot
distinguish ZCTA 10069's arithmetically- and substantively-correct
162,659/sq mi from an error. Running a screen with no domain knowledge in
it is precisely how we got 9,578 flagged ZCTAs and zero information.

**Winkler reframes it as prioritisation rather than detection.** RR99-01
§1 on selective (macro) editing: the measures used, such as the
Hidiroglu-Berthelot statistic, "determine which records cause the largest
deviations of key totals in the survey population. Follow-up is more
efficient because the most important records are reviewed first." And the
proportionality principle from the same section: "If only a few published
totals need to be accurate, then an efficient use of resources may be to
perform detailed edits on only a few records that effect the estimated
totals."

Our published total is the 2,333-ZCTA cost ranking. So the screen should
rank rows by **influence on the published number** and be reviewed
top-down until the reviewer stops finding errors. Manhattan is
high-influence and correct, survives review once, and is never looked at
again. Water Mill at $68,623/month is high-influence and contaminated, and
goes in front of a human. A robust-z screen puts 9,578 rows in front of a
human and is therefore never run at all.

**Van den Broeck supplies the verdicts.** Every flagged extreme gets one of
four diagnoses — erroneous, true extreme, true normal (the prior
expectation was wrong), or idiopathic (no explanation found, still
suspect). The prose above already assigns them without naming them:

```
  ZCTA 10069, 162,659 people/sq mi     TRUE EXTREME   keep; "true extreme
                                                      values should always
                                                      stay in the analysis"
  three ZCTAs above 10,000 sq mi       TRUE EXTREME   keep
  cost_per_parcel $6.41 at ZCTA 83650  TRUE EXTREME   keep
  rent_index $68,623/mo, Water Mill    ERRONEOUS      correct if a correct
                                                      value can be found,
                                                      otherwise delete AND
                                                      REPORT
  permits_yoy_pct = -100%, 6,232 rows  TRUE NORMAL,   fix the DERIVED
                                       prior wrong    VARIABLE (denominator
                                                      floor), not the data
  traffic_proximity = 14,529,474       IDIOPATHIC     until the units
                                                      question (F7) is
                                                      answered
```

Two design consequences for R9. It should emit a **diagnosis column, not a
flag** — the pipeline being declared plausibility band (Rahm & Do) ->
influence ranking (Winkler) -> four-way diagnosis (Van den Broeck) ->
treatment by diagnosis. And it should use **two thresholds per column, not
one**: Van den Broeck's soft cutoff flags for diagnosis, the hard cutoff
diagnoses error immediately (his Figure 2).

**And the threshold goes in the output.** The 2019 tools survey documents
five tools returning five different answers to "give me the quartiles of
this column", three of them not quartiles, and closes by demanding "clear
declaration of the parameters used". "28.36% of ZCTAs are outliers" is
exactly the unreproducible number that paper is about. "28.36% of 33,772
ZCTAs have |modified z| > 3.5 on household density, modified z computed on
the median and MAD" is not.

One last reassurance and one last caveat. The reassurance: the same survey
found that **no** tool among thirteen — including market leaders — supports
multivariate or model-based outlier detection, and four offer only an
unlabelled plot you cannot drill into. Our gap is the market's gap. The
caveat, from Van den Broeck: in small samples "statistical outlier
detection ... may become less valid", while "examination of data tables will
be more effective". For the 43- and 104-row facility files, sort the table
and read it. That is Box 2, screening method three, and it would have found
F4 in a minute.

### F7. Three joins present a coarse geography under a fine column name

`warehouse/optional.py:67-80` rolls EJScreen tracts up to counties, with a
correct and well-argued comment (population-weighted, because "an
unweighted mean lets a 200-person tract count as much as a 9,000-person
one"). It then joins county to ZCTA. The result is five columns that look
like ZCTA attributes and are county attributes:

```
  column                  source grain     distinct values   ZCTAs   ZCTAs
                                                                   per value
  ------------------------------------------------------------------------
  pm25                    EJScreen tract             3,082  33,012      10.7
  diesel_pm               EJScreen tract             3,165  33,241      10.5
  traffic_proximity       EJScreen tract             3,139  33,486      10.7
  low_income_pct          EJScreen tract             3,195  33,486      10.5
  people_of_colour_pct    EJScreen tract             3,193  33,486      10.5
  permit_units_total      BPS county                 2,639  32,965      12.5
  electricity_cents_kwh   EIA state                  1,279  33,642      26.3
  wage_light_truck_driver BLS OES CBSA                 349  18,475      52.9
```

86,082 tracts were read to produce 3,195 numbers. A ZCTA-level model
regressing anything on `pm25` is really regressing on a county fixed
effect with 3,195 levels, and its standard errors — computed as if there
were 33,012 independent observations — are wrong by roughly sqrt(10.5).
The wage columns are the extreme case: fifty-three ZCTAs share each value.

The code knows this. The comment at optional.py:63-66 states it plainly.
What is missing is any trace of it in the *data*: no `_grain` suffix, no
companion column recording the source geography, nothing that would stop a
reader of `panel.parquet` treating `pm25` as a ZCTA measurement.

This is Rahm & Do's "inconsistent aggregating" class, detected and untreated.

### F8. A 2018Q1 row carries data from 2025

Vintages, read off `common/config.py` and the filenames in
`experiments/superseded-artefacts/external_check.json`:

```
  source          vintage on disk                    grain     time-varying
  ------------------------------------------------------------------------
  TIGER Gazetteer 2020 ZCTA delineation              ZCTA      no
  ACS 5-year      2023 release (pools 2019-2023)     ZCTA      no
  CBP             2022                               ZIP       no
  EJScreen        EJScreen_2024_Tract_*.csv.zip      tract     no
  BLS OES         oesm25ma.zip  (May 2025)           CBSA      no
  BPS permits     2023 config, 2018-2025 on disk     county    YES
  Zillow ZORI     monthly                            ZCTA      YES
  Zillow ZHVI     monthly                            ZCTA      YES
  EIA             monthly                            state     YES
```

Every row labelled `2018Q1` therefore asserts May-2025 metro wages,
2024 environmental indicators, 2019-2023 pooled demographics, 2022 business
counts and 2020 boundaries as contemporaneous facts about the first quarter
of 2018. The spread between the earliest and latest vintage inside a single
row is seven years.

Measured consequence:

```
  numeric / boolean panel columns                       35
  time-varying (differ across quarters within a ZCTA)    9
  time-invariant (identical in all 32 quarters)         26
  nominal panel rows                             1,081,312
  independent draws for a time-invariant column     33,791  (32x inflation)
```

`warehouse/panel.py`'s docstring is honest about the design — "levels ...
pinned vintages, not a time series" — and the decision to keep the panel
dense rather than filter to observed rows is the right one, for exactly
the sample-selection reason the docstring gives. The finding is not that
the design is wrong. It is that **nothing carries the vintage into the
data**, so no consumer can tell that `wage_freight_handler` in a 2018 row
is a 2025 number, and no model can be prevented from reading 1,081,312
rows as 1,081,312 observations.

Two specific hazards follow:

- `data/interim/bls_wages.parquet` has no year column at all. The vintage
  exists only in the source ZIP's filename. If `oesm24ma.zip` were dropped
  in tomorrow, nothing in the pipeline would notice or record the change.
- Any backtest that trains through 2023 and predicts 2024-2025
  (`config.BACKTEST_TRAIN_THROUGH`) is training on covariates that include
  May-2025 wages. That is look-ahead leakage in the strict sense. It is
  probably small — metro wage ranks are stable — but it is unmeasured and
  it is structural, not accidental.

### F9. Complete-case analysis is the default at four places, unmeasured at three

**The sharpest citation for this finding turns out to be from 1976.**
Fellegi & Holt §1 enumerate five options when a record fails an edit, and
option 5 is ours — "Drop all records which fail any of the edits or at
least omit them from analyses using fields involved in failed edits." Their
verdict, written the same year Rubin published *Inference and missing data*
and therefore before MCAR had a name:

> "Option 5 would involve an implicit assumption that the statistical
> inferences are unaffected by such deletions. This is equivalent to
> assuming that the deleted records have the same distribution as the
> satisfactory records. If such an assumption must be made it would seem
> much more sensible to make it through imputation techniques."

That is the MCAR assumption stated in plain language, and F1 measures it
failing: the stratum where `rent_index` is present has a median household
density 63.6x the stratum where it is absent.

Note what they are *not* saying. They are comparing deletion against
imputation for **edit failures**, where the record is otherwise complete.
Ours is a 94.3%-missing covariate, and §4 below still declines to impute
it, for a reason they would recognise: imputing 94% of a column from the 6%
that is a systematically different kind of place produces a column that
looks like data and is a regression prediction.

What the cleaning literature does ask for here, and we do not do:

- **Report the deletion as data, not as a log line.** Five Facets §3.3 and
  §A.7: "transformations on missing values, like deleted records or applied
  imputation strategies, must also be part of the metadata"; "Missing
  tuples can also result from previous transformation strategies, such as
  deleting them if they contain missing values."
- **Report the outcome both ways.** Van den Broeck, Treatment Phase:
  "separate analyses with and without remaining outliers and/or with and
  without imputation", and the reporting standard's "differences in outcome
  with and without remaining outliers". This is the cheap, decisive move
  and it has never been run.
- **Name it as a representativity failure**, not only a statistical one.
  Five Facets §A.22, and EU AI Act Article 10, which names representativity
  alongside accuracy, completeness and relevancy as regulated dimensions.

And one point where Van den Broeck is more permissive than we assumed:
deletion is the *prescribed* treatment for an impossible value whose
correct value cannot be recovered — "Impossible values are never left
unchanged, but should be corrected if a correct value can be found,
otherwise they should be deleted." The 55 zero-population ZCTAs dropped at
`cost/runner.py:57` arguably qualify (a cost per parcel with a zero
denominator is impossible) and the drop is logged, so that site is nearly
compliant. The other 23 dropped ZCTAs have people and no households, which
is not impossible but group quarters, and deleting those is not covered.

Every drop and imputation in the pipeline, with a measured count:

```
  site                              rule                    measured effect
  -------------------------------------------------------------------------
  cost/runner.py:57                 households.fillna(0)>0  drops 80 of
                                                            2,413 pilot
                                                            ZCTAs (3.32%).
                                                            LOGGED.
  cost/daganzo.py:91                income.fillna(
                                      reference_income)     51 of 2,333
                                                            (2.19%).
                                                            FLAGGED in the
                                                            output as
                                                            income_imputed.
  cost/daganzo.py:152               linehaul.fillna(
                                      default 25 mi)        0 rows today.
  cost/runner.py:166                notna().all(axis=1)     0 rows today.
                                                            COUNTED+PRINTED.
  viz/charts_economics.py:63        dropna(subset=...)      0 rows today.
                                                            COUNTED+LOGGED.
  viz/charts_economics.py:164       dropna(cost_per_parcel) 0 rows today.
  viz/charts_density.py:57          dropna + >0 filter      not measured
                                                            here; guards a
                                                            log axis only.
  models/panel_source.py:144        dropna(subset=
                                      REAL_COVARIATES)      drops 131 of
                                                            2,206 units
                                                            (5.94%).
                                                            RECORDED in the
                                                            report detail.
  warehouse/facilities.py:118       open_quarter.fillna(1)  19 of 43 (44.2%).
                                                            NOT measured
                                                            at the point of
                                                            edit. See F5.
  warehouse/facilities.py:215       enabled.fillna(False)   collapses
                                                            unknown into
                                                            negative. See F5.
```

The two that bind:

**`cost/runner.py:57`** drops 80 pilot ZCTAs. The dropped and kept strata
are not comparable:

```
                            dropped (80)      kept (2,333)
  median population                    0            21,417
  median land area, sq mi          0.069             6.890
  median income                      n/a           103,950
```

Of the 80, 55 have zero population and 23 have population but zero
households — the F3 group-quarters problem. The rationale in the comment is
sound (infinite cost per parcel sorts to the bottom of an ascending rank
and looks like the most expensive place rather than an empty one). The
missing step is deciding what the 23 inhabited-but-householdless ZCTAs
are. Right now the code says "no demand" about places with people in them.

**`models/panel_source.py:144`** drops 131 of 2,206 in-scope ZCTAs (5.94%)
for having any of `households`, `median_household_income` or
`establishments` missing:

```
                            dropped (131)   kept (2,075)
  median population                    42         21,805
  median households                     0          8,372
  median household density            0.0        1,169.2
  median land area, sq mi             0.2            6.4
  median income                    69,534        106,857
  median establishments              25.5          546.0
  ever enabled                    67 (51.1%)  1,131 (54.5%)
```

Credit where it is due: the docstring at panel_source.py:131-138 is the
single best piece of missing-data reasoning in the repo. It states that the
drop happens here rather than inside `hazard.design`, records the counts in
`detail`, and observes that because ACS is pinned and repeated, "a ZCTA is
missing a covariate for all of its quarters or for none of them; the drop
removes whole units and never punches a hole in the middle of one unit's
history". That last claim is verifiable and I verified it: 26 of 35 numeric
columns are constant within ZCTA, so the drop is unit-level. Good.

And the *event-rate* bias is mild: 51.1% of dropped units were ever enabled
against 54.5% of kept, and the 67 lost units are 5.6% of all ever-enabled
in-scope units. So this drop does not badly distort the outcome. What it
distorts is the covariate support — the model never sees a single ZCTA
below about 500 people. That is defensible (they are not candidate sites)
but it is an undeclared scope restriction, not a data-cleaning decision, and
it is not stated anywhere a reader of the results would find it.

### F10. Referential integrity is never reported, and one join loses 58% of its keys

All unmatched rates, computed for this audit. "Discarded" means rows on the
source side that no key on the spine claims:

```
  join                                        left   matched  unmatched
  ------------------------------------------------------------------------
  gazetteer ZCTA -> zcta_county crosswalk    33,791   33,791    0 ( 0.00%)
  gazetteer ZCTA -> ACS5 2023                33,791   33,772   19 ( 0.06%)
  gazetteer ZCTA -> CBP                      33,791   30,928 2,863 ( 8.47%)
  gazetteer ZCTA -> Zillow ZHVI              33,791   26,262 7,529 (22.28%)
  gazetteer ZCTA -> Zillow ZORI              33,791    8,544 25,247(74.72%)
  county -> BPS permits                       3,211    3,011  200 ( 6.23%)
  county -> EJScreen county rollup            3,211    3,195   16 ( 0.50%)
  county -> CBSA delineation                  3,211    1,895 1,316 (40.98%)
  panel cbsa_code -> BLS OES area_code          928      388  540 (58.19%)
  panel cbsa_code -> ACS1 metro                 928      523  405 (43.64%)
  panel state -> EIA state                       56       51    5 ( 8.93%)
  ---- rows DISCARDED from the source side ----
  CBP ZIP not in the gazetteer               35,002   30,928 4,074 (11.64%)
  ACS5 ZCTA not in the gazetteer             33,772   33,772    0 ( 0.00%)
  Zillow ZORI ZCTA not in the gazetteer       8,547    8,544    3 ( 0.04%)
  Zillow ZHVI ZCTA not in the gazetteer      26,269   26,262    7 ( 0.03%)
  BPS county not in the crosswalk             3,043    3,011   32 ( 1.05%)
  BLS OES area not in the panel                 393      388    5 ( 1.27%)
```

Most of these are coverage, not key breakage, and the two large ones have
innocent explanations that the code already documents:

- The 40.98% county miss is structural: the OMB delineation only lists
  counties that belong to a CBSA, so 1,316 rural counties correctly have no
  CBSA. That flows through to 26.80% of ZCTAs having `cbsa_code` NULL.
- The 11.64% CBP discard is also correct and is the reason
  `warehouse/schema.py:build_dim_zcta` joins outward from the gazetteer:
  CBP knows about point ZIPs and retired vintages that are not ZCTAs.
  The comment says so explicitly.

The one that hurts is **BLS OES: 540 of 928 CBSAs unmatched (58.19%)**,
which is what produces the 45.33% missingness on all five wage columns. It
is not a key bug — the join is on `cbsa_code`, which optional.py:44-48
records as a deliberate fix from a title-based join that landed only
325 of 708. It is that OES publishes about 393 metro areas against the
delineation's 928, and the 540 it omits are micropolitan and small. So the
wage covariates are missing exactly where the missingness correlates with
size:

```
                         wage columns present   wage columns missing
  median household dens.        139.1/sqmi              9.9/sqmi   (14.0x)
  median population                  8,185                 1,101
  median income                     78,709                62,138
```

Same shape as F1, at 14x instead of 64x. Again MAR on density, again not
MCAR, again unanalysed.

**The finding is not any individual rate. It is that none of these numbers
is computed by the pipeline.** `experiments/superseded-artefacts/panel_report.json` reports
percent non-null per column, which is the *symptom*. Nothing reports which
join produced it, so "45% of wages are missing" cannot be traced to
"OES covers 388 of our 928 CBSAs" without an audit like this one.

### F11. Environmental and energy missingness runs the *opposite* way

Worth separating out, because it is the one place where the naive
assumption ("missing means rural") is wrong:

```
  column                 % ZCTAs   hh density    hh density   direction
                         missing   where present where missing
  --------------------------------------------------------------------
  traffic_proximity        0.90%       28.3          206.8    missing is
  low_income_pct           0.90%       28.3          206.8    7.3x DENSER
  people_of_colour_pct     0.90%       28.3          206.8
  diesel_pm                1.63%       28.8           56.3
  pm25                     2.31%       28.4           95.2
  electricity_cents_kwh    0.44%       28.6          340.1    12x DENSER
  diesel_usd_gal           0.44%       28.6          340.1
```

Cause, by state:

```
  electricity / diesel missing (149 ZCTAs):  PR 132, GU 7, VI 6, MP 3, AS 1
  traffic_proximity missing (305 ZCTAs):     CT 288, GU 7, VI 6, MP 3, AS 1
  diesel_pm missing (550 ZCTAs):             CT 288, AK 245, + territories
  pm25 missing (779 ZCTAs):                  CT 288, AK 245, PR 132, HI 97,
                                             + territories
```

So it is not a density mechanism at all — it is two clean coverage rules
(EIA does not publish state series for the territories; EJScreen's 2024
release drops Alaska and Hawaii on some indicators) plus one genuine data
problem: **all 288 Connecticut ZCTAs are missing every EJScreen column.**
Connecticut replaced its eight legacy counties with nine planning regions
for the 2022 vintage, changing the county FIPS codes. The EJScreen tract
GEOIDs use the new codes and `zcta_county.parquet` uses the old ones, or
vice versa, and the county-grain join at optional.py:70 silently returns
nothing. Nobody noticed because the loss is 0.9% of rows.

This is Rahm & Do's "wrong references" class arriving through a real-world
geography change, and it is the kind of thing a referential-integrity
report (see F10) catches on the day it happens.

---

## 3. What this project does well

An audit that only finds fault is not an audit. Several things here are
better than the norm for a capstone and a couple are better than the norm
for production code. Each with evidence.

**The grain contract is real and it holds.** `warehouse/panel.py:168`,
`assert_grain`, fails the build unless the panel is exactly one row per
(zcta, date_id). Verified: 1,081,312 rows, 1,081,312 distinct pairs,
33,791 x 32 = 1,081,312 exactly, zero fully duplicated rows. The docstring
is unusually honest about *why* it exists ("It holds today because
ingest.normalise de-duplicates both sources, which makes the panel correct
by luck rather than by contract. This is the contract."). That sentence is
the difference between a test and an assertion of faith. There is a
matching unit test, `tests/unit/test_panel_grain.py`.

**The record linkage is properly done and properly cited.**
`common/linkage.py` implements Fellegi-Sunter's three-way decision rule
(match / review / non-match), cites Winkler RR99-04 for it, and then
*declines* to implement the likelihood ratio — giving the paper's own
reasons (§3.1 on lists with high typographical error and moderate overlap,
§3.4 on Belin-Rubin needing calibration data we do not have). Declining to
implement something for a reason found in the source is a higher standard
than implementing it. Three further details worth naming:

- The thresholds `STREET_MATCH = 0.92` and `STREET_REVIEW = 0.78` are
  measured off an actual sweep of the 516-address OSHA extract
  (`ingest/address_audit.py --sweep`), and the docstring prints the bimodal
  distribution with the empty gap they sit in. Borrowed thresholds are the
  norm; measured ones are not.
- The Jaro transcription error in the printed paper is caught and corrected
  in the docstring, with the reason.
- Three-valued slot comparison (agree / missing / conflict) is what keeps
  `1555 N CHRISMAN RD` and `1555 S CHRISMAN RD` apart. That is Winkler's
  §2.3 case 3 handled correctly rather than collapsed to a boolean.

Independently re-run for this audit against `national_facilities.csv`: 5
candidate pairs generated, 3 matched at score 1.000, 2 correctly rejected,
0 false positives. The module does what it claims.

**The OSHA namesake filter is a real entity-resolution step, not a string
match.** `ingest/osha.py` requires both a name match and a NAICS prefix in
the warehousing set, rejects a maintained namesake list, logs how many were
rejected with examples, and — most usefully — `earliest_by_site` collapses
inspections to buildings via `linkage.link` rather than exact string
equality, with an explicit conservative rule: an unplaceable record stays
as its own group, because "a spurious extra row is visible in the count and
a wrong merge is not". That asymmetry argument is correct and is the right
default for this problem.

**Zero-padding discipline is consistent and it works.** ZCTA and
county_geoid are zero-padded to 5 at every entry point
(`census_api.py:100`, `normalise_geo.py:36-37`,
`normalise_external.py:207`). Verified: 2,583 ZCTAs with a leading zero
survive intact in the panel, 0 malformed keys of any kind. This is the most
common silent-data-loss bug in ZIP-level work and it has been closed.
`warehouse/facilities.py:97` reads the facility CSV with `dtype=str` and
comments that this is "the single most common way this file arrives
damaged" — correctly, since a default `pd.read_csv` of
`national_facilities.csv` parses `zip` as int64 and destroys the leading
zero on 8 of 104 rows (02019, 02149, 02062, 01569, 01887, 08215, 08360,
02907). The active path is safe; the file is a trap for anything else.

**The ACS sentinel map is complete.** `census_api.py:31-33` maps six
negative sentinel codes to NULL. Verified: 0 negative values survive in
`population`, `households`, `median_household_income`, `median_home_value`
or `median_age`, and 0 infinities anywhere in the panel. The only negative
values in the whole file are longitudes (all of them), 32 latitude rows
(American Samoa, -14.32), and the two year-on-year percentage columns.

**`rent_observed` is textbook.** Rather than imputing an 89%-missing column
or dropping the rows, the panel emits an explicit availability indicator,
and the comment names the exact failure it prevents: a tree learning
"Zillow has no listing here" as a proxy for rural. Verified to equal
`rent_index.notna()` exactly. This is the one place in the project where a
missing-data mechanism was reasoned about before the fact.

**Density by construction, rather than filtering to observed rows.** The
panel is a full cross join of 33,791 ZCTAs and 32 quarters, and the
docstring gives the reason: "Filtering to observed rows here would quietly
hand the model a sample-selection bug, because the sources with the best
coverage (Zillow, BPS) are the urban ones." That is the correct instinct
and it is the opposite of what most pipelines do.

**Imputation provenance where it exists.** `cost/daganzo.py:220` emits
`income_imputed` alongside the result; verified True on exactly the 51 rows
where income was NULL. `normalise_external.py:83-93` distinguishes an
explicit BLS sentinel (`*`, `#`) from an ordinary blank and records
`wage_suppressed`. Both are the right pattern, and since 2026-09-14 the same
pattern reaches the panel for the ACS top- and bottom-codes and for
`open_quarter` as well, enforced by `warehouse/flag_gate.py`. The remaining
gap (F2) is no longer that the flags are dropped; it is that nothing
downstream reads any of the seven.

**Drops are counted out loud.** `cost/runner.py:59`,
`cost/runner.py:167-169`, `viz/charts_economics.py:66-70` and
`models/panel_source.py:145-152` all count what they removed and either log
it or put it in the report JSON. Several carry a comment explaining the
specific wrong-but-believable chart the drop prevents. That is Van den
Broeck's diagnosis stage being taken seriously even where the treatment
stage is thin.

**Refusing an uncertain join.** `warehouse/optional.py` skips any source
whose grain it cannot infer, with a warning, and never shadows an existing
column. The stated rule — "a source that cannot be joined confidently is
skipped with a warning, never guessed at. A missing column is obvious in
the coverage report; a wrong join is a plausible number nobody questions" —
is exactly right, and the BLS title-to-code fix documented at
optional.py:44-48 (325 of 708 matched on titles, versus 388 of 393 source
rows placed on codes) is a case of the principle paying off.

---

## 4. Remediation, prioritised

Split by whether it changes a published number. Effort is calendar time for
one person who knows the codebase.

### Changes a result

```
  R1  A declared sentinel registry, carried to the panel as censoring
      indicators.  REVISED 2026-09-13.  MOSTLY DONE 2026-09-14: F2, F5
      common/sentinels.py is the registry, warehouse/flag_gate.py is
      the gate, and seven flags now reach the panel including the two
      bottom-codes and open_quarter_imputed.  What is STILL OPEN is the
      second half of the effort estimate below -- deciding what
      daganzo.py does with a bound rather than a measurement.  No
      consumer conditions on any flag, so the "affects" line below is
      unchanged and no published number has moved.
      Literature: Rahm & Do Table 2 "missing values" (dummy values --
      NOT "embedded values", which is what this entry used to say; see
      section 1.1).  Table 3 gives the detection rule: "presence of
      default value may indicate real value is missing".  Van den Broeck,
      Diagnostic Phase: "Substitute code values for missing data should
      be corrected before analysis."  Five Facets section 3.3: the
      placeholder set is itself metadata and must be documented per
      source.
      What changed: this is no longer "propagate four booleans".  It is
      one registry naming every sentinel per source, applied at ingest,
      converting to NULL + indicator, with the indicator carried to the
      panel as a CODE that an edit can refer to (Fellegi & Holt section 2
      note 3a).  It subsumes R3, because open_quarter.fillna(1) is the
      same class.
      Effort: half a day for the registry and the ingest change; half a
      day to decide and document what daganzo.py should do with a bound
      rather than a measurement.
      Affects: 36 of 2,333 ZCTAs in the headline ranking on income, 46 on
      home value, plus two bottom-code flags nobody has ever made, plus
      19 of 43 facility rows.

  R2  Adjudicate the three contradicting facility records.        F4
      CORRECTED 2026-09-13.  The ACTION below was right; the
      justification was wrong and is replaced.
      Literature: Fellegi-Holt.  Corollary 2's minimum-change criterion
      selects the FIELD to change -- here, uniquely, open_q_index -- and
      asserts that satisfying values exist.  It does NOT select the
      value; the edits admit both dates equally.  Section 7 supplies the
      rule for choosing: an a priori reliability weight per source
      ("take the set with the lowest product of a priori weights"),
      with their own coded-vs-self-reported intuition mapping onto
      OSHA-inspection-date vs permit record.  Where the sources rank
      equal, section 1 option 2 applies: "avoid 'manufacturing' data
      instead of collecting it."  Full derivation in F4 above.
      This entry previously read "the minimum change is one date per
      pair", which conflates choosing a field with choosing a value.
      Effort: half a day.  Declare the edit; declare the provenance
      ranking in FACILITY_PANEL_PROVENANCE.md; three permit lookups.
      Then add the matcher to the build as a hard failure (it already
      exists and already finds them), and add the missing test over
      national_facilities.csv alongside the one at test_linkage.py:212.
      Note Rahm & Do's fifth process phase, backflow: the adjudicated
      dates need a durable home outside src/, or the next refresh of
      national_facilities.csv silently undoes them.
      Affects: three fifteen-mile Los Angeles / Stockton / Portland
      catchments switch on 10, 6 and 3 quarters later. Given that one
      station switches on a median of 58 ZIPs, this moves on the order of
      170 ZCTA-quarters of the target -- and min() moves them all in the
      same direction, which is bias, not noise.

  R3  Stop defaulting an unknown opening quarter to Q1, or carry the
      flag.  NOW A SUB-CASE OF R1.  HALF DONE 2026-09-14.          F5
      Literature: Van den Broeck's reversibility requirement, stated in
      his own terms -- the first diagnostic procedure is "to go to
      previous stages of the data flow to see whether a value is
      consistently the same.  This requires access to well-archived and
      documented data with justifications for any changes made at any
      stage."  We could not run it because the NULL was destroyed at
      load.  We can now: open_quarter keeps its NULL and
      open_quarter_imputed reaches the panel on 433 ZCTAs.  The flag is
      carried and no model reads it, so the Q1 artefact is unchanged.
      Effort: the 2 hours to add `open_quarter_imputed` is spent.  What
      is left is threading it into the model, and half a day
      for the cheap decisive move the paper actually asks for: fit with
      and without the 19 imputed-quarter facilities and publish the
      difference, rather than defending a default.
      Affects: 44.2% of facility rows, producing 35.47% of events in Q1
      against 25% expected. The project already measures this artefact in
      hazard_report.json and does nothing with it.

  R4  Fix the Connecticut EJScreen join.                          F11
      Literature: Rahm & Do "wrong references" — a key that resolves to
      nothing because the two sides use different vintages of the same
      code system.
      Effort: 2-3 hours. Connecticut's 2022 planning-region FIPS need a
      crosswalk to the legacy county codes on one side of
      optional.py:70.
      Affects: 288 ZCTAs x 5 environmental columns x 32 quarters =
      46,080 cells currently NULL that should not be.

  R5  Decide what the 353 population-without-households ZCTAs are, and
      the 23 of them that reach the cost model.                   F3, F9
      Literature: Fellegi-Holt again — this is a violated attribute
      dependency and the right response is a declared edit plus a
      documented resolution, not a filter at the point of use.
      Effort: 2 hours to classify (group quarters are identifiable from
      ACS table B26001 if it is worth fetching); the decision itself is
      substantive, not technical.
      Affects: 23 of 2,413 pilot ZCTAs currently dropped with no reason
      recorded beyond "no households".
```

### Hygiene — does not move a number today, prevents one moving silently tomorrow

```
  R6  A declared edit set, run as a build gate, PLUS the three pieces
      this entry used to omit.  EXPANDED 2026-09-13.            F3
      Literature: Fellegi & Holt's central proposal -- edits as a formal,
      inspectable set of constraints over fields in normal form, checked
      together rather than scattered as filters.  Winkler RR99-01 section
      2 lists four features of such a system; three of them are separable
      from the solver and cost hours.  The twenty-two edits in section F3
      are already written; they need a home.
      One thing the reading settles cheaply: Fellegi & Holt section 5.1 --
      "as far as editing only is concerned, implied edits need not be
      considered -- if the initially stated explicit edits all pass, no
      implied edit can fail."  So a DETECTION-ONLY gate is complete
      without any of the expensive machinery.  Implied edits buy
      correction, not detection.
      Effort, itemised:
        declared edit set + report JSON + Makefile target      1 day
        consistency check over the edit set                    2-3 hours
          Winkler's feature 2, "checked prior to the receipt of data".
          Ours is the cheap version: does any single field have a
          permissible value that fails an edit regardless of the others?
          A genuine FH consistency check needs implied-edit generation
          and would catch contradictions through a chain of three; ours
          will not.  SAY SO IN THE CODE COMMENT.
        invalid-code convention                                3-4 hours
          Fellegi & Holt section 2 notes 3a and 6.  Fixes the 19-ZCTA
          false positive and the enabled.fillna(False) collapse.  See F3.
        the three logs                                         half a day
          Fellegi & Holt section 6.1 items 5-7: per-record edit failures,
          per-edit record counts, and -- the one we had never thought of
          -- the uncorrected data preserved and cross-tabulated against
          the corrected.  Item 7 answers "what did cleaning do to the
          results?", which the project currently cannot answer at all.
        reviewing the 22 edits with Winkler's
          "an edit is a compromise" in mind                    half a day
          At least one is already known wrong; expect to delete two or
          three.  This is NOT free and was not costed before.
                                                          TOTAL ~3 days
      The trap already found stands: an edit must distinguish "violated"
      from "vacuously true because the field is NULL", or it fires on the
      19 gazetteer-only ZCTAs and nobody believes it again.  The
      invalid-code convention above is the fix.

  R7  A referential-integrity report: unmatched rate on every join, both
      directions, written to outputs/metrics/.                    F10, F11
      Literature: Rahm & Do list referential integrity as a first-class
      single-source schema problem; the point of reporting both
      directions is that the discarded side is invisible otherwise.
      Effort: half a day. The eighteen numbers in F10 were computed in
      about forty lines.
      Value: this is what would have caught Connecticut on day one, and
      what makes "45% of wages are missing" traceable to "OES covers 388
      of our 928 CBSAs" without an audit.

  R8  Carry the vintage into the data.                            F8
      Literature: Rahm & Do "inconsistent timing"; the standard remedy is
      to make the temporal grain of each attribute explicit rather than
      implicit in the join.
      Effort: 2 hours for a source-vintage table written next to the
      panel; longer if you want a `_vintage` column per source-derived
      block. At minimum, add a year column to bls_wages.parquet, which
      currently records its vintage only in a ZIP filename.

  R9  A screen that ranks by influence and emits a DIAGNOSIS, not a
      flag.  REDESIGNED 2026-09-13 -- the old design was a robust-z
      report and would have produced 9,578 rows of noise.        F6
      Literature, three papers pointing the same way:
        Rahm & Do Table 3 -- the detection rule for illegal values is
          "max, min should not be outside of permissible range" and
          "variance, deviation ... should not be higher than threshold".
          A DECLARED plausibility band per column, not a distributional
          screen.  A robust-z has no domain knowledge in it and so
          cannot tell Manhattan from an error.
        Winkler RR99-01 section 1 -- selective (macro) editing.  The
          Hidiroglu-Berthelot measures "determine which records cause
          the largest deviations of key totals"; "the most important
          records are reviewed first".  Rank by influence on the
          published cost ranking, not by distance from the median.
        Van den Broeck -- four diagnoses per point (erroneous / true
          extreme / true normal / idiopathic), and two thresholds per
          column (soft flags for diagnosis, hard diagnoses error).
      Design: plausibility band -> influence rank -> four-way diagnosis
      -> treatment by diagnosis.  Output a diagnosis column and the
      thresholds used, per the 2019 tools survey's closing demand for
      "clear declaration of the parameters used".
      Effort: 1-2 days, up from half a day, because the bands and the
      influence measure have to be thought about rather than computed.
      Do NOT winsorise: section F6 shows the extremes are mostly
      Manhattan, and a 3-sigma filter would delete the answer.
      Value: it would surface the Hamptons ZORI contamination (126 rows
      above $10,000/month across 8 ZCTAs) and the permits_yoy_pct
      denominator problem (6,232 rows at exactly -100%) without anyone
      having to go looking -- and it would classify the second of those
      as a derived-variable design fault rather than a data fault, which
      a z-score cannot do.
      For the 43- and 104-row facility files, do not do this at all.
      Van den Broeck: in small samples "statistical outlier detection
      ... may become less valid", while "examination of data tables will
      be more effective".  Sort the table and read it.

  R10 A grain suffix or companion column on broadcast values.     F7
      Literature: Rahm & Do "inconsistent aggregating".
      Effort: 1-2 hours to rename or annotate eight columns. Cheap, and
      it is the difference between a reader knowing that pm25 is a county
      mean and a reader assuming it is a ZCTA measurement.

  R11 Reconcile or retire the second home-value series.           F1 scorecard
      Two independent measures of the same quantity sit in the panel
      (median_home_value from ACS, home_value from Zillow ZHVI). They
      correlate at 0.951 in logs but 17.2% of 24,675 ZCTAs differ by more
      than 25% and 5.3% by more than 50%. Either state which is
      authoritative for what, or build the reconciliation.
      Effort: 2 hours to document; a day if you want a blended series.

  R12 Rename the three "metro" columns.                           F7 scorecard
      `metro` (Zillow, 708 labels), `cbsa_title` (OMB, 928 labels) and
      `metro_label` (project registry) disagree for 2,343 of the 8,349
      ZCTAs where the first two both exist (28.1%). This already caused
      one measured defect (the 325-of-708 BLS title join). It will cause
      another.
      Effort: 1 hour.
```

### Not worth doing

```
  Multiple imputation of rent_index. The mechanism is MAR on density
  (F1), so MI is formally available — but no model currently uses the
  column, and imputing 94% of a variable from the 6% that is a different
  kind of place would produce a column that looks like data and is a
  regression prediction. Carry rent_observed, which already exists, and
  say the coverage rate out loud.

  Filtering outliers. See R9. The extremes are real.

  Full Fellegi-Holt implied-edit generation and minimum-change
  imputation.  Conclusion unchanged; REASONING REPLACED 2026-09-13,
  because the old reasoning was a cost argument and the source
  contradicts it.
    Winkler RR99-01 section 2 says a non-programmer can stand up a
    production edit system for a small, well-understood survey "in less
    than one day", and his whole section 1 is that formal editing is
    CHEAPER TO OWN than if-then-else rules.  So arguing from cost loses.
    (The week is the ENGINE, not the edit table, and we would be its only
    user.)
    The argument that works is correctness, from Winkler section 3.1 on
    what happened when SPEER shipped with only some implicit edits
    generated: "the set of fields designated for change can no longer be
    guaranteed to be the error-localization solution ... Indeed, it can
    no longer even assure that the solution of fields to change will
    yield a record that satisfies all edits."  A partial Fellegi-Holt
    system does not degrade gracefully -- it returns something that looks
    like a minimum-change solution, is not, and may not satisfy the
    edits.  Against a plain declared list, which makes no such claim, a
    half-built solver is STRICTLY WORSE.  Winkler's summary of the
    theory: "all implicit edits are always needed."
    Feasibility is not the obstacle and we should say so.  On Winkler's
    own bounds our 22 edits over ~15 numeric fields sit nowhere near the
    exp(exp(250)) regime that defeats the Census -- ratio edits over n
    fields admit at most n(n-1)/2 in total, 105 for n=15.  We could
    generate them.  There is simply exactly one place in this project
    where error localisation tells us something we cannot see by
    inspection, and it is three facility records whose minimal cover is
    a single field and is obvious on paper (F4).
    Declare the edits (R6, now including the consistency check, the
    invalid-code convention and the three logs); skip the solver.

  A data-quality dimension scorecard (accuracy / completeness /
  consistency / timeliness with metrics).  Added 2026-09-13.
    The 2019 survey of 667 tools found that across thirteen evaluated
    products -- including Informatica, SAS, Oracle and Talend -- ZERO
    implement a consistency metric, ZERO implement a timeliness metric,
    and ONE implements accuracy, only against a user-supplied gold
    standard.  Two vendors could not explain how their own metrics
    worked.  The authors conclude: "In practice, DQ dimensions are used
    to group domain-specific DQ rules (sometimes referred to as metrics)
    on a higher level."  That is the structure this document already has
    -- a taxonomy used to GROUP concrete checks -- and it is a defensible
    position rather than a shortcut.  Do not build the scorecard.
```

---

## 5. The one-paragraph answer

The pipeline is stronger on *schema* discipline than almost anything at
this scale — the grain contract holds exactly, keys are well-formed,
zero-padding is intact, sources are refused rather than guessed at, and the
record linkage is implemented from a paper the author clearly read. It is
weak on *instance* discipline: there is no formal edit set, no outlier
screening of any kind, no missingness-mechanism analysis, and no
referential-integrity reporting, so problems are caught when someone goes
looking rather than when they arrive. The three specific defects that
change a published number are censoring codes read as measurements (F2 —
since 2026-09-14 the flags are declared, carried to the panel and enforced by
a build gate, but no model or cost function conditions on one, so the number
is unchanged), three facility records that contradict each other about the
opening
date and are resolved silently in favour of the earlier one (F4), and an
unknown-quarter default that has put ten points of spurious Q1 seasonality
into the outcome variable (F5) — a defect the project already measures and
has not acted on. None of the three is expensive to fix. All three would be
caught by the same build gate — and that gate now exists
(`warehouse/flag_gate.py`), which is why F2 and F5 are recorded above as
half-closed rather than open. Half-closed changes nothing a reader sees: the
values are flagged and still consumed as measurements.

**And one sentence added after reading the papers.** F2 and F5 are not two
defects but one: a dummy value occupying a field that should say "unknown",
invisible to every check we run because the value is plausible. Rahm & Do
Table 2 calls it *missing values*; Van den Broeck calls the mechanism an
*erroneous inlier* and correctly predicts that it "will often escape
detection"; the current literature calls it a *hidden missing value* and
has a detector for it. One declared per-source sentinel registry closes
both. That reclassification is the single most useful thing the reading
produced, and it was only possible because the papers were opened rather
than recalled.
