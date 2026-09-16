# Notes — Fellegi & Holt (1976), Automatic Edit and Imputation

*Read in full 2026-09-13, including the Appendix proofs. These notes exist
so nobody has to open the PDF again.*

---

## 1. Citation and local file

```
  I. P. Fellegi and D. Holt.
  "A Systematic Approach to Automatic Edit and Imputation."
  Journal of the American Statistical Association, 71(353):17-35,
  March 1976.  Applications Section.
  JSTOR stable URL: https://www.jstor.org/stable/2285726
  Received May 1973.  Revised June 1975.

  Local file:  ../Research/2285726.pdf   (20 PDF pages)
  PDF page 1 is the JSTOR cover sheet.  PDF page 2 = printed p. 17.
  So: printed page + (-15) = PDF page.  Printed p. 35 = PDF page 20.
```

Affiliations at the time: Fellegi was assistant chief statistician of
Canada, Statistical Services Field, Statistics Canada. Holt was a lecturer
in the Department of Econometrics and Social Statistics, University of
Southampton. The acknowledgment credits R. Graves and M. Podehl for
implementing the generalised system at Statistics Canada.

This is the same Fellegi as Fellegi-Sunter record linkage (1969), but this
is a *different* paper about a *different* problem. Edit and imputation is
not record linkage. `src/siting_atlas/common/linkage.py` cites
Fellegi-Sunter; nothing in the repo currently implements this paper.

---

## 2. What the paper is for

It is the founding paper of automatic edit and imputation. It solves one
problem precisely: **given a set of declared constraints ("edits") and a
record that violates some of them, which fields do you change?** Before
this paper, editing was a pile of hand-written if-then-else corrections,
independently specified from the edits they were supposed to satisfy, with
no guarantee that a corrected record would pass. Fellegi and Holt prove
that if you first derive the *logically implied* edits, then you can always
find a minimal set of fields whose alteration makes the record satisfy
every edit — and the imputation rules fall out of the edits themselves, so
you never specify them separately.

The paper is mostly about **qualitative (coded) data**. Linear arithmetic
edits are handled and Theorem 3 covers them, but the authors say the
implementation strategy of Sections 4-5 "is likely to be practicable as
stated only for logical edits" (Sec. 2, note 4).

---

## 3. Section-by-section walkthrough

### Section 1 — Introduction (printed pp. 17-19)

#### What "editing" means, formally

The definition is given as a two-part A/B split (printed p. 17):

> "By editing we mean
>
> A. the checking of each field of every survey record (the recorded answer
> to every question on the questionnaire) to ascertain whether it contains
> a valid entry; and
>
> B. the checking of entries in certain predetermined combinations of
> fields to ascertain whether the entries are consistent with one another."

Type A is a single-field validity check ("age should not be blank or
negative; marital status should not be blank; number of children should be
less than 20"). Type B is a cross-field consistency check, and it is the
interesting one:

> "Conceptually, edits of Type B specify in one form or another sets of
> values for specified combinations of fields which are jointly
> unacceptable (or, equivalently, sets of values which are jointly
> acceptable)." (Sec. 1)

Type A edits are "immediate consequences of the questionnaire and code
structure"; Type B edits "are usually specified on the basis of extensive
knowledge of the subject matter of the survey."

#### The five options when a record fails

Quoted in full, because option 5 is the one that indicts complete-case
deletion (printed p. 17):

> "When a record fails some of the edits, we have, theoretically, five
> options:
>
> 1. Check the original questionnaires in the hope that the original
> questionnaire is correct and the edit failures are caused by coding error
> or error introduced during the conversion of data to machine-readable
> form;
>
> 2. Contact the original respondent to obtain the correct response (or
> verify that the reported response was correct in its original form);
>
> 3. Have clerical staff 'correct' the questionnaire using certain rules
> which would remove the inconsistencies;
>
> 4. Use the computer to 'correct' the questionnaire, also using certain
> rules which would remove the inconsistencies;
>
> 5. Drop all records which fail any of the edits or at least omit them
> from analyses using fields involved in failed edits."

And then, immediately, the argument against option 5 — written in 1976,
which is the same year Rubin published "Inference and missing data" and
therefore predates the MCAR/MAR/MNAR vocabulary:

> "Option 5 would involve an implicit assumption that the statistical
> inferences are unaffected by such deletions. This is equivalent to
> assuming that the deleted records have the same distribution as the
> satisfactory records. If such an assumption must be made it would seem
> much more sensible to make it through imputation techniques. At any rate,
> when population totals have to be estimated, some form of correction
> would still be necessary: if the correction is not made through explicit
> imputation, it would have to be made through some form of weighting.
> However, implicit in weighting is the imputation of the appropriate mean
> to all fields of all records which are involved in failed edits. We
> believe that a better imputation results if we make use of the valid
> parts of questionnaires and impute for as few fields as possible."
> (Sec. 1, printed p. 17)

On preferring 2 over everything:

> "Corrections of Type 1 and 2, particularly 2, are certainly worthwhile if
> feasible: one should, whenever possible, avoid 'manufacturing' data
> instead of collecting it." (Sec. 1)

On preferring 4 over 3: "Contrary to clerks, the computer applies the rules
consistently and fast".

#### The complaint that motivates the whole paper

> "Edit and correction rules are often more or less independently specified
> with no full assurance that the corrections will render the data
> consistent with respect to the edits. Also, in the absence of some
> overall philosophy of correction and in the light of the very complex
> rules often used, the net impact of the corrections on the data is
> unforeseeable and, what is possibly even worse, not readily capable of a
> systematic post-implementation evaluation." (Sec. 1, printed p. 18)

#### THE THREE CRITERIA

These are the paper's stated aims. There are exactly three, and they are
given twice — once in the abstract and once in Section 1 — **in different
orders**. The Section 1 version is the authoritative one and is the order
Winkler RR99-01 uses. Quoted in full from printed p. 18:

> "There are three criteria for imputation of qualitative data which we
> have attempted to meet, the first of which is overridingly important in
> the rest of this article.
>
> 1. The data in each record should be made to satisfy all edits by
> changing the fewest possible items of data (fields). This we believe to
> be in agreement with the idea of keeping the maximum amount of original
> data unchanged, subject to the constraints of the edits, and so
> manufacturing as little data as possible. At the same time, if errors are
> comparatively rare, it seems more likely that we will identify the truly
> erroneous fields. This criterion appears to be reasonable, particularly
> for qualitative (coded) data, since it provides the only feasible measure
> of the extent of changes due to imputations.
>
> 2. It should not be necessary to specify imputation rules; they should
> derive automatically from the edit rules. This would insure that imputed
> values will not continue to fail edits, simplify the task of specifying
> edits and imputations, simplify their computer implementation, facilitate
> the implementation of subsequent changes to specifications, and generally
> lead to a more controlled operation.
>
> 3. When imputation takes place, it is desirable to maintain, as far as
> possible, the marginal and even preferably the joint frequency
> distributions of the variables, as reflected by the 'correct' records,
> i.e., those which pass the edits."

The abstract's ordering, for completeness, puts the frequency-structure
criterion second and the derived-imputation-rules criterion third. The
substance is identical. Criterion 1 is the **minimum-change criterion**.

Criterion 3 is illustrated: if labour-force status is in error, we know
only that the record belongs to the subpopulation with the same age, sex
and occupation, so the logical inference is the average labour-force status
of that subpopulation — "since the average of a set of codes does not make
sense, we replace the average by a code value randomly selected from this
subpopulation." Even for quantitative variables a drawn value beats the
mean, "since imputing the average repeatedly would distort the
distributions."

Footnote 1 defines imputation:

> "By imputation for a given record we mean changing the values in some of
> its fields to possible alternatives with a view to insuring that the
> resultant data record satisfies all edits. To the extent that an
> originally recorded value may be an invalid blank, the term encompasses
> data correction necessitated by partial nonresponse or by prior clerical
> editing."

Closing warning of Section 1, which is worth reading before anyone cites
this paper as a licence to invent data:

> "we emphasize that the motivation for this article is not to make editing
> and imputation so simple and routine as to tempt survey takers and
> processors to replace direct observation and measurement by computer
> imputations. ... While the amount of imputation is thus minimized, it may
> still be unacceptably high in particular surveys ... we strongly recommend
> that this impact be studied in the context of the particular
> applications."

### Section 2 — The normal form of edits (printed pp. 19-21)

Notation. Each record has N fields. `A_i` is the set of possible code
values for field i. A record `a` having in field i a code belonging to some
subset `A_i^0` is written `a` in `A_i^0` (formally a Cartesian product; the
paper simplifies the notation deliberately).

**Definition of an edit.** The combination of code values across fields
which are unacceptable is a subset of the code space:

```
    f(A_1^0, A_2^0, ..., A_N^0)                                   (2.2)
```

where f connects the subsets by intersection and union, and

> "The function f thus defines a subset of the code space and becomes an
> edit if, through some prior knowledge, it is declared a set of
> unacceptable code combinations, in the sense that a record a is said to
> fail the edit specified by f whenever a is in f(A_1^0, ..., A_N^0)."
> (Sec. 2, eq. 2.3)

**The normal form.** Applying the distributive law reduces any f to a union
of intersections (2.4), and a record fails f iff it is in any one of the
bracketed intersections. So any edit breaks into a series of edits of the
form

```
    a in  INTERSECTION over i in s of  A_i*                        (2.5)

    written        INTERSECTION_{i in s} A_i*  =  F                (2.6)

    or, padding out with A_i* = A_i for every field i not in s:

                   INTERSECTION_{i=1..N} A_i*  =  F                (2.7)
```

Equations (2.6) and (2.7) **are** the normal form. Field i is said to
**enter an edit explicitly** if `A_i*` is a *proper* subset of `A_i`.

The plain-language gloss, which is the sentence to quote:

> "What (2.5) states is perhaps intuitively obvious: any edit, whatever its
> original form, can be broken down into a series of statements of the form
> 'a specified combination of code values is not permissible.'" (Sec. 2)

The edits as specified by subject-matter experts, in normal form, are the
**explicit edits**, "to distinguish them from logically implied edits — a
concept to be introduced later" (Sec. 2, note 2).

**Note 3** answers "how much extra work does the normal form impose on the
experts?". Two statement types are handled:

- (a) *Simple validation edits*. Expand each field's code set with a single
  extra code `c_i` representing all invalid codes; replace every invalid
  code (including invalid blanks) with `c_i` at load; then the normal-form
  edits `{c_i} = F` for i = 1..N are equivalent.
- (b) *Consistency edits* of the form "Whenever a is in f(...), then it
  should follow that a is in g(...)". Take the complement of g; then the
  statement is equivalent to "Whenever a is in f INTERSECT complement(g),
  the record fails the edit", which is (2.3), which converts to normal form.

The authors note the conversion is a pure Boolean-algebra algorithm that
could be automated, but "we decided not to implement it, but rather ask our
subject-matter experts to adhere to the extremely simple syntax provided by
the normal form", and report that the normal form "was, precisely due to
its simplicity, fully embraced by subject-matter experts".

**Note 4** distinguishes logical edits (finite code sets) from quantitative
/ arithmetic edits (continuous scale). Both can be cast in normal form, so
Section 3's theory applies to both; but the normal form is not the natural
form for arithmetic edits, and "the implementation strategy of Sections 4
and 5 ... is likely to be practicable as stated only for logical edits."

A linear arithmetic edit `0 <= M(a_1,...,a_N)` (failure condition) becomes,
after solving for a_1 with nonzero coefficient, `a_1 >= L(a_2,...,a_N)`, and
then the normal-form set `A_1^0 INTERSECT A_2^0 INTERSECT ... = F` with
`A_1^0 = {a_1 : a_1 >= L(...)}` and each other `A_i^0 = {a_i}` — one such
edit per possible choice of the other values. Worked farm example: fields
a1 = cultivated acres, a2 = unimproved acres, a3 = total acres; the edit
`a1 + a2 != a3` becomes `{a3 : a3 != a1+a2} INTERSECT {a1} INTERSECT {a2} =
F` for all a1, a2 >= 0.

**Note 5** — continuous fields can be discretised for editing. If income
enters only two edits distinguishing 5,000-10,000 and 7,000-12,000, the
edits require distinguishing only five ranges (0-4,999; 5,000-6,999;
7,000-10,000; 10,001-12,000; 12,000+), and income can be treated as a
five-code qualitative field.

**Note 6** — the invalid-entry convention:

> "We accept a convention that whenever one of the fields of a record
> contains an invalid entry (i.e., one which is not among the set of
> possible values), we consider the record as failing all edits which that
> field enters explicitly." (Sec. 2, note 6)

And: "The code value 'blank' may or may not be among the set of possible
(i.e., permissible) values of a field; e.g., blank in the income field
might be a possible value in a general population survey, whereas blank in
the age field would not be a possible value."

**Worked normal-form conversion** (end of Sec. 2). The original edit: "If a
person's age is < 15 years or he (she) is an elementary school student,
then relationship to head of household should not be head and marital
status should be single." Converted in five steps to four normal-form
edits:

```
  (Age < 15)            and (Head)       = Failure
  (Age < 15)            and (not Single) = Failure
  (Elementary School)   and (Head)       = Failure
  (Elementary School)   and (not Single) = Failure
```

"The last four statements together are equivalent to the originally
specified edit. They are in the normal form."

### Section 3 — The complete set of edits (printed pp. 21-25)

The problem statement:

> "Unfortunately, generally one knows only which edits are failed, but not
> which fields are causing the edit failures. In this section we will try
> to build a bridge leading to an inference from the knowledge of the edits
> which failed to the identification of the fields which need to be
> changed to remove the edit failures." (Sec. 3)

#### Example 1 — why implied edits are necessary

Three fields. Age in {0-14, 15+}. Marital Status in {Single, Married,
Divorced, Widowed, Separated}. Relationship to Head in {Head, Spouse of
Head, Other}. Two explicit edits:

```
  I   (Age = 0-14) INTERSECT (Mar. Stat. = Ever married)          = F
  II  (Mar. Stat. = Not Now Married) INTERSECT (Rel. to Head = Spouse) = F
```

where Ever Married = {Married, Divorced, Widowed, Separated} and Not Now
Married = {Single, Divorced, Widowed, Separated}.

Record: Age = 0-14, Marital Status = Married, Rel. to Head = Spouse. It
fails I, passes II. Try to fix by changing Marital Status: *every* marital
status code fails one or the other edit. The hidden conflict is between Age
and Relationship to Head, and it is named by the logically implied edit:

```
  III (Age = 0-14) INTERSECT (Rel. to Head = Spouse)              = F
```

> "The point to note in this example is the importance of identifying,
> together with the initial edits (Edits I and II), the logically implied
> edit (Edit III). Edits I and II only suffice to identify that the current
> record is subject to a conflict. However, it is only after having
> identified the logically implied Edit III that we are in a position to
> determine systematically the field(s) which have to be changed to remove
> all inconsistencies." (Sec. 3)

With III in hand, the record fails I and III. The fields that "cover off"
the failed edits are: the single field Age, or any two of the three, or all
three. Changing Age to 15+ alone gives a conflict-free record.

> "In such a situation one can argue that the combined evidence presented
> by all the fields together seems to point to the single field of Age
> being in error, rather than some combination of two fields being in
> error." (Sec. 3)

#### Example 2 — the same thing with arithmetic edits

Four quantitative fields a, b, c, d. Two edits (failure conditions):

```
  I   a - b + c + d < 0
  II  -a + 2b - 3c >= 0     [paper writes 2b >= a + 3c]
```

Record a=3, b=4, c=6, d=1 passes I, fails II. Three implied edits, each a
positive linear combination of I and II:

```
  III  b - 2c + d < 0
  IV   a - c + 2d < 0
  V    2a - b + 3d <= 0
```

Now II, III and IV fail; I and V pass. Variable c enters every failed edit,
and is the only single variable that does. "changing c to any value between
zero and 5/3 will result in a record which satisfies all the edits, e.g.,
c = 1 would be a suitable imputation."

#### THE LEMMA (edit generation)

Stated exactly (Sec. 3, printed p. 23):

> "**Lemma:** If e_r are edits for all r in s where s is any index set,
>
> ```
>   e_r :  INTERSECTION_{j=1..N} A_j^r = F     for all r in s
> ```
>
> Then, for an arbitrary choice of i (1 <= i <= N), the expression
>
> ```
>   e* :   INTERSECTION_{j=1..N} A_j* = F                        (3.1)
> ```
>
> is an implied edit, provided that none of the sets A_j* is empty, where
>
> ```
>   A_j* = INTERSECTION_{r in s} A_j^r      for j != i
>   A_i* = UNION_{r in s} A_i^r
> ```
> "

In words: pick a **generating field** i. For every other field, intersect
the code sets across the contributing edits. For the generating field,
*union* them. The proof is in the Appendix and is three lines: any point on
the left side of (3.1) is included in the left side of one of the `e_r` and
so is an edit failure.

> "It is relevant to emphasize that the edits e_r (r in s) in the statement
> of the Lemma may represent any subset of the set of edits."

The edits contributing to a derived edit are called **contributing edits**,
and "implied edits, once derived, can participate in the derivation of
further implied edits."

#### DEFINITION: essentially new implied edit

> "If all the sets A_j^r are proper subsets of A_j, the complete set of
> code values for Field j, but
>
> ```
>   A_i* = A_i
> ```
>
> then the implied edit (3.1) is said to be an **essentially new edit**. In
> fact, in this case (3.1) does not involve all the fields explicitly
> involved in the e_r (Field i being explicitly involved in the Edit e_r
> but not in (3.1)). Field i is referred to as the **generating field** of
> the implied edit." (Sec. 3, immediately after the Lemma)

Worked on Example 1: generating on Marital Status gives `A_3* = (Ever
Married) UNION (Not Now Married) = (any code)`, while `A_1* = (Age = 0-14)`
and `A_2* = (Rel. to Head = Spouse)`. So e* is edit III, and it *is*
essentially new. Generating on Age instead gives `(Age = any code)
INTERSECT (Rel. to Head = Spouse) INTERSECT (Mar. Stat. = Divorced,
Widowed, Separated) = F`, which is **not** essentially new, "because in one
of the edits (e2) the generating field (Age) is represented by the set of
all possible codes for that field. Intuitively ... it is simply a weaker
form of e2 and, thus, does not add to our understanding of the constraints
imposed by the edits on the data."

#### DEFINITION: complete set of edits

> "The set of explicit (initially specified) edits, together with the set
> of all essentially new implied edits, is said to constitute a **complete
> set of edits** and is denoted by OMEGA. Clearly, any finite set of
> explicit edits corresponds to a complete set of edits." (Sec. 3)

`OMEGA_K` is the subset of OMEGA involving only fields 1..K — formally,
those edits for which `A_j^r = A_j` for all j > K.

#### Theorem 1

> "**Theorem 1:** If a_i^0 (i = 1, 2, ..., K-1) are, respectively, some
> possible values for the first K-1 fields, and if these values satisfy all
> edits in OMEGA_{K-1}, then there exists some value a_K^0 such that the
> values a_i^0 (i = 1, 2, ..., K) satisfy all edits in OMEGA_K."

Proof by contradiction in the Appendix. The authors note explicitly:

> "We just note here that it depends on the set of edits being complete
> with respect to the essentially new implied edits, but not necessarily
> all possible implied edits."

That qualifier matters: completeness is required with respect to
*essentially new* implied edits only, which is what makes generation
finite.

#### Corollary 1

If fields 1..K-1 have values satisfying all edits in OMEGA_{K-1}, then
there exist values for fields K..N such that the whole record satisfies all
edits. "The proof follows immediately by repeated application of Theorem 1."

#### Corollary 2 — THE MINIMUM-CHANGE RESULT

> "**Corollary 2:** Suppose that a record (questionnaire) has N fields
> having the values a_i (i = 1, ..., N). Suppose that S is a subset of
> these fields having the property that at least one of the values a_i
> (i in S) appears in each failed edit, i.e., in each edit failed by the
> given record. Then values a_i^0 (i in S) exist such that the imputed
> record consisting of the values a_i (i not in S), together with a_i^0
> (i in S), satisfies all edits."

And the operational reading, which is the paragraph to quote when someone
asks what "minimum change" actually means:

> "We have only to select any set of fields having the property that at
> least one of them is involved in each failed edit and it then follows
> that a set of values exists for these fields which, together with the
> unchanged values of the other fields, will result in an imputed record
> satisfying all edits. If the set of fields which we select is the set
> containing the smallest number of fields (minimal set), then Corollary 2
> states that by changing the values in these fields (but keeping values in
> other fields unchanged) we will be able to satisfy all the edits. Thus,
> if we have a complete set of edits, Corollary 2 provides an operational
> procedure whereby, given a questionnaire, the smallest number of fields
> can be identified, which, if changed, will result in all edits being
> satisfied by the given questionnaire." (Sec. 3)

**Read that twice.** Corollary 2 identifies the *fields*. It asserts that
suitable *values* exist. It does not tell you which value to pick. Choosing
the value is Section 4, and where the edits do not pin it down, Section 7.

#### Theorem 2 — the generation procedure is exhaustive

> "**Theorem 2:** If e_p : INTERSECTION_{i=1..N} A_i^p = F is an edit which
> is logically implied by the explicit edits, then it can be generated by
> the edit generation procedure of the Lemma."

Proof in the Appendix, by constructing, for each value of a_N in A_N^p, an
explicit failed edit, generating on field N, then on N-1, and so on down to
field 1, producing an edit whose code sets contain those of e_p.

#### DEFINITION: an inconsistent set of edits

The last paragraph of Section 3, and one of the most practically useful
results in the paper:

> "a set of edits is said to be inconsistent if they jointly imply that
> there are permissible values of a single field which would automatically
> cause edit failures, irrespective of the values in the other fields
> (clearly, such values should not be in the set of possible values for the
> field). Thus, an inconsistent set of edits means that there is an implied
> edit e_r of the form
>
> ```
>   e_r :  A_i^r = F
> ```
>
> where A_i^r is a proper subset of the set of possible values for some
> Field i. However, if A_i^r is a subset of the possible values of Field i,
> then this edit could not be an originally specified edit. Since the edit
> generating process identifies all implied edits, it follows that this
> edit will also be generated. It is a simple matter to computer check the
> complete set of edits to identify implied edits of this type and, thus,
> to determine whether the set of originally specified edits is
> inconsistent." (Sec. 3)

With the preceding clarification that edits "cannot, in themselves, be
contradictory. They can, however, contradict the initial field by field
identification of permissible code values."

### Section 4 — Imputation (printed pp. 25-27)

Corollary 2 gives the fields; this section gives the values. Both methods
are **hot-deck**: "imputing for a field of the current record the value
recorded in the same field of some other record which, however, passed all
the relevant edits. This method attempts to maintain the distribution of
the data as represented by the records which passed the edits." Assume
fields 1..K are the minimal set to impute, and a complete set of edits.

#### Method 1 — Sequential imputation

Impute field K first, then K-1, ..., down to 1. Consider the M edits in
which field K is specifically involved but fields 1..K-1 are not. Discard
those the record already satisfies because of its values in fields
K+1..N — these cannot be broken by whatever we put in field K. Of the
remaining M' edits, the imputed value must satisfy

```
    a_K*  in   INTERSECTION_{r=1..M'}  complement(A_K^r)          (4.2)
```

where the complement is taken with respect to `A_K`. This set is never
empty: if it were, Theorem 1 says there would be a failed edit involving
only fields K+1..N, contradicting the choice of the minimal set.

Having fixed field K, all edits involving field K and the untouched fields
are satisfied; move to K-1, and so on.

Worked Example 3. Five fields: Sex {Male, Female}; Age {0-14, 15-16, 17+};
Mar. Stat. {Single, Married, Divorced, Separated, Widowed}; Rel. to Head
{Wife, Husband, Son or Daughter, Other}; Education {None, Elementary,
Secondary, Post-secondary}. Five edits, stated to be a complete set:

```
  e1: (Sex = Male)              INTERSECT (Rel. Head = Wife)            = F
  e2: (Age = 0-14)              INTERSECT (Mar. Stat. = Ever Married)   = F
  e3: (Mar. Stat. = Not Married) INTERSECT (Rel. Head = Spouse)         = F
  e4: (Age = 0-14)              INTERSECT (Rel. Head = Spouse)          = F
  e5: (Age = 0-16)              INTERSECT (Educ. = Post-secondary)      = F
```

Current record: Sex = Male, Age = 12, Mar. Stat. = Married, Rel. Head =
Wife, Educ. = Elementary. Edits e1, e2, e4 fail. No single field covers all
three. Three covering pairs: {Sex, Age}, {Age, Rel. to Head}, {Mar. Stat.,
Rel. to Head}. Suppose Sex and Age are chosen (K = 2). Imputing Age: edits
involving Age but not Sex are e2, e4, e5; e5 is satisfied because Education
!= Post-secondary, so M' = 2; `a_2*` must be in complement(A_2^2) INTERSECT
complement(A_2^4) = (Age = 15+). Impute, say, 22. Then Sex: only e1
involves Sex, `a_1*` must be in complement(A_1^1) = (Sex = Not Male), so
Female.

The actual value is drawn from previously accepted records:

> "Having determined from (4.2) the set of acceptable values, one of which
> must be imputed, we search (with a random starting point) among the
> records which passed all edits or among those which were already imputed
> but for which the given field was not imputed. We accept as the current
> imputed value for each field the first acceptable values (as defined by
> (4.2)) encountered during the search. By so doing, the various acceptable
> values will be chosen with probability proportional to their occurrence
> in the population as a whole, as long as the errors among the original
> records occur more or less in random order." (Sec. 4)

Stated disadvantage: fields are imputed one by one, so "the joint
distribution of values imputed to individual fields will be different from
that in the population (except when the distributions involved are
independent), although their marginal distribution will be the same. This
last disadvantage is true of most sequential imputation methods."

Edge case: if at some point no failed edit involves field k without also
involving remaining fields k-1..1, "we may simply impute any value for
Field k and then continue with Field k-1."

#### Method 2 — Joint imputation

Consider the M" edits the record can potentially fail depending on the
imputed values for fields 1..K. For each field i in K+1..N that is *not*
being imputed, form

```
    A_i*  =  INTERSECTION_{r=1..M"}  A_i^r                         (4.3)
```

These sets are never empty (they contain at least the record's own value).
Then find any previously accepted record whose values in fields K+1..N fall
inside those sets, and copy its values for fields 1..K wholesale. Because
that donor record satisfies all edits, the imputation automatically
satisfies all edits.

On Example 3: `A_3* = (Mar. Stat. = Ever Married)`, `A_4* = (Rel. Head =
Wife)`, `A_5* = (Education = any code)`. Search the clean records for one
with an Ever Married marital status and Rel. to Head = Wife, any education;
copy its Sex and Age.

Method 2's advantage over Method 1:

> "Since the imputation is done jointly for the K fields, it is not just
> the values of the single fields which will now appear in the same
> proportions as in the population, but also the incidence of combinations
> of values. Thus, no longer is there a danger of imputing into the same
> record two reasonably common values which almost never occur together."

Its cost is a longer donor search. "the system implemented at Statistics
Canada uses Method 2 as the main imputation procedure, with Method 1 as a
default option."

Both methods can be tightened with fields not linked by any edit: "one
might as an additional constraint only impute income from records which
have the same sex, age and occupation, even though there may be no explicit
edit linking income with these fields."

### Section 5 — Implementation procedures (printed pp. 27-32)

#### 5.1 Applying logical edits to a record — the logical edit matrix

Represent both edits and records as bit strings. One column per possible
code; a group of columns per field. For each edit, enter 1 for every code
in that field's code set and 0 elsewhere. **Table 1** is the resulting
matrix for Example 3: 18 columns (2 Sex + 3 Age + 5 Mar. Stat. + 4 Rel. to
Head + 4 Education) x 5 edit rows plus one current-record row. The current
record has exactly one 1 per field.

> "the current record fails an edit if and only if all the 1's of the data
> record are overlaid on 1's in the row corresponding to that edit. Put
> differently, if an edit is viewed as a vector of 0's and 1's ... and if
> the current record is similarly viewed, the data record would fail an
> edit if and only if the scalar product of the two vectors is equal to the
> number of fields (five, in this example)." (Sec. 5.1)

Faster equivalent (Table 2): select from the edit matrix only the columns
corresponding to the record's actual code values, one per field, then take
the product across each row. Product 1 = failed, 0 = passed.

Two reading rules:

- A field represented by all 1's in an edit row means the edit passes or
  fails irrespective of that field's code.
- "No edit can be represented by a set of 0's for all code values in a
  field, since this would imply that the edit could not be failed by any
  record."

Single-field validation edits fit the same representation: add an extra
"Invalid" code column per field; the validity edit for Sex is a 1 in Sex's
Invalid column, 0 in the other Sex columns, and 1 everywhere else.

And a performance note with a sting in it:

> "Note that, as far as editing only is concerned, implied edits need not
> be considered — if the initially stated explicit edits all pass, no
> implied edit can fail. ... Nevertheless, when we come to imputation, the
> implied edits become relevant." (Sec. 5.1)

That is: you need implied edits to *fix* records, not to *find* them.

#### 5.2 Deriving a complete set of logical edits

The Lemma in bit-matrix form. Pick contributing edits and a generating
field. For every field except the generating field: enter 0 for a code if
*any* contributing edit has 0 there; 1 only if *all* have 1. For the
generating field this is reversed: 1 if *any* contributing edit has 1; 0
only if *all* have 0.

The new edit is a valid essentially new implied edit **unless**:

```
  1. One of the fields contains all 0's.
  2. The generating field does not contain all 1's.
  3. The new edit is already contained in an existing edit.
```

Condition 3 is checked easily: "for the new edit to be redundant, there
must be an edit already identified which has a 1 in every location where
the new edit has a 1."

Three screening rules to avoid combinatorial waste:

```
  1. For any set of edits to produce an essentially new edit, they must
     have a field in common which is specifically involved in each of them
     (through a proper subset of its values).
  2. No essentially new edit will be produced from an implied edit and a
     subset of the edits from which it was itself generated.
  3. A combination of edits using a particular Field i as the generating
     field need not be considered if some subset of the proposed
     combination using the same Field i has already resulted in an
     essentially new implied edit.
```

Plus the reminders: "any new edit which involves just one field indicates
that the original explicit edits are themselves inconsistent", and "having
derived all implied edits, it is necessary to add the single field valid
code checks to form the complete set of logical edits."

The timing argument, which is the whole case for a consistency check:

> "Note that the consistency of the edits is validated at the edit
> generation stage before data processing begins, when corrections are
> easily made, rather than at the data processing stage when, through a
> chance combination of data values, the belated discovery of the existence
> of inconsistencies could cause extensive dislocation of processing
> schedules, together, possibly, with the need to reformulate the edits and
> reprocess the data." (Sec. 5.2)

#### 5.3 Deriving a complete set of arithmetic edits

A linear edit expressing failure is `f(a_1,...,a_N) >= 0`, described by N+1
coefficients plus an indicator b_r (1 = strict inequality, 0 = weak).
Standardise so the first nonzero coefficient is +/-1. The section restricts
itself to the case where fields divide cleanly into logical-only and
arithmetic-only.

> "**Theorem 3:** An essentially new implied edit e_t is generated from
> edits e_r and e_s using Field i as a generating field if and only if
> a_i^r and a_i^s are both nonzero and of opposite sign. The coefficients
> of the new edit, a_k^t, are given by
>
> ```
>   a_k^t = a_k^s * a_i^r  -  a_k^r * a_i^s ;   k = 0, 1, ..., N
> ```
>
> where r and s are so chosen that a_i^r > 0 and a_i^s < 0. These
> coefficients of the new edit need to be standardized by making the first
> nonzero coefficient equal to +/-1."

> "In effect, the theorem simply states that from two linear inequalities
> where the inequality signs are in the same direction, a variable can be
> eliminated by taking their linear combinations if and only if the
> variable has coefficients in the two inequalities which are of the
> opposite sign."

This is Fourier-Motzkin elimination, not named as such. The paper states
that repeated application of Theorem 3 derives all essentially new implied
arithmetic edits, and that "The proof follows directly from that of Theorem
2, but it is rather cumbersome and will be omitted."

#### 5.4 Identifying the minimal set of fields — THE SET COVER

Build the **failed edit matrix**: R' rows (the failed edits in the complete
set, including single-field edits) x N columns (fields). Cell (r,n) = 1 if
field n is specifically involved in failed edit r, else 0.

> "The problem of identifying the smallest number of fields to be changed
> to make all edits satisfied is now reduced to the problem of choosing the
> smallest set of fields (columns) which together have at least 1 in each
> failed edit (row)." (Sec. 5.4)

That is the minimum set cover problem, stated in 1976 without the name.

The proposed algorithm:

```
  1. All satisfied edits may be ignored (rows containing zeros only).
  2. Identify all fields failing single field edits (validity checks,
     incorrect blanks, etc.). By definition these must be included in the
     minimal set. All failed edits which explicitly involve these fields
     will now be covered off, so we can generate a modified failed edit
     matrix by deleting all edits in which the chosen fields appear
     explicitly. If no edits remain, the minimal set has been identified.
  3. If Step 2 did not eliminate all edits, identify the edit involving the
     fewest fields (select an edit arbitrarily if there is a tie). At least
     one of the fields involved in this edit must be in the minimal set.
  4. For each such field generate a modified failed edit matrix as in Step
     2. Keep a record of the combination of fields so far selected.
  5. Repeat Steps 3 and 4 until the first modified failed edit matrix
     vanishes.
```

Worked on a second Example 3 record (Sex = Male, Age = 0-14, Mar. Stat. =
Divorced, Rel. to Head = Wife, Educ. = Post-secondary), all five edits
fail; the algorithm branches through two cycles and terminates with the
minimal set {Rel. to Head, Age}. The authors note "in this simple example
the result could be directly verified from the first failed edit matrix:
Rel. to Head and Age between them cover off all failed edits, but no other
pair of fields does", and concede "Other approaches may be developed to the
problem which could well be more efficient."

#### 5.5 Imputation in the matrix representation

Methods 1 and 2 re-expressed as column operations on Table 1. Method 1,
step 2: combine the relevant edit rows column-by-column with an OR (1 if
any row has 1), then any code where the result is **0** is an acceptable
imputation. Method 2, step 2: for each field not imputed, AND the relevant
edit rows (the codes with 1 in every relevant edit), giving the donor
search ranges.

### Section 6 — The benefits of the proposed method (printed pp. 32-33)

Grouped under three headings. The methodological list is the one to quote.

**6.1 Methodological benefits** (all seven, quoted):

> "1. The approach provides an orderly framework and philosophy for the
> development of edit and imputation procedures for surveys, in the sense
> that all procedures follow consistently and, largely, predictably from
> the edit specifications provided by subject-matter experts.
>
> 2. The procedure preserves the maximum amount of reported data, in that
> it minimizes the amount of imputation.
>
> 3. The procedure guarantees that records which have already been
> corrected will satisfy all the edit constraints.
>
> 4. Imputations are based on full information, i.e., the imputation of any
> field of a current record takes advantage of all the reported information
> of that record which is not subject to imputation (and which is logically
> related, through the edits, to the fields to be imputed).
>
> 5. For each questionnaire a log can be kept of all edits failed. This
> facilitates subsequent evaluation and the tracing of specific edit and
> imputation actions.
>
> 6. For each edit statement a log can be kept of all questionnaires
> failing it.
>
> 7. The uncorrected data can be preserved and cross-tabulated with the
> corrected data."

Items 5, 6 and 7 are the audit trail, specified in 1976. And the reason
they matter:

> "The major significance of these advantages lies in their evaluation
> possibilities. For example, a sample of questionnaires can be edited and
> imputed before the processing of the bulk of the survey data begins. If
> it turns out that some particular edits are failed by an inordinately
> large proportion of records, one would become suspicious of either the
> validity of the particular edit, the field procedures followed, or the
> ability of respondents to answer some particular questions. Similarly,
> cross-tabulation of uncorrected data with corrected data can provide
> revealing early feedback on the likely gross and net effect of
> imputations." (Sec. 6.1)

**6.2 Systems-oriented benefits.** A generalised system can be developed
independently of any subject-matter application (and was, at Statistics
Canada). The problem is completely defined and so straightforward to
implement. The approach separates three modular stages: "analysis of edits
(in the form of derivation of implied edits); editing ...; and, finally,
imputation."

**6.3 Subject-matter benefits.** Experts can run experimental edit
specifications without systems work. Specifications need not be integrated
flowcharts or decision tables but "completely independent statements of the
variety of conditions which should be considered as edit failures", so
several experts can work simultaneously — "an important consideration in
the case of multisubject surveys, such as a census". Only edits need
specifying, not imputations. And feedback starts before any data exists:

> "The first feedback, in fact, can take place prior to the availability of
> any data. When edits are specified by subject-matter experts, these are
> first analyzed to derive all essentially new implied edits. The implied
> edits are available for review. They have been found to be very useful in
> practice. Clearly, whenever an implied edit is judged inappropriate, at
> least one of the originally specified edits must also be inappropriate."
> (Sec. 6.3, item 4)

### Section 7 — Further considerations (printed p. 33)

Short, and disproportionately important for us.

**Nonuniqueness of the minimal set.**

> "There is no reason that the method of obtaining the smallest set of
> fields, described in Section 3, should lead to a unique solution. In
> fact, it is quite possible that more than one minimal set of fields can
> be identified."

Three ways to break the tie are offered. First, if Method 2 is used,
identify all minimal sets and "accept that set which can be imputed soonest
in the search" — trading search cost for arbitrariness. Or "one could much
more simply arbitrarily or randomly decide between the alternatives."

**A priori weighting of fields for reliability.** The substantive answer:

> "It often happens that one has an a priori belief that some fields are
> less likely to be in error than others. If one field is the product of a
> complicated coding operation and the other is a self-coded response,
> then, intuitively, one is inclined to believe that the simple self-coded
> response is more likely to be error-free. By and large we have not tried
> to quantify this, believing that the data alone, by identifying the
> smallest possible set of fields to be changed, would more readily
> indicate the fields most likely to be in error. However, where there is
> more than one minimal set of fields, an a priori weight of the
> reliability of each field could easily be used to select among the
> minimal sets of fields the one to be imputed. For example, we could
> simply take the set with the lowest product of a priori weights."

And a stronger version:

> "Note that one could carry further the notion of a priori weights to the
> extent of choosing not the smallest number of fields which would convert
> all failed edits to satisfied ones, but rather the set with the smallest
> product of weights. The method of selecting the minimal set (see Section
> 5) can easily be modified to accommodate this change."

**An empirical alternative to subjective weights:**

> "Instead of using a priori weights, one can edit the records in one pass
> through the computer and determine for each field the proportion of edits
> entered by the fields which are failed. This may provide a less
> subjective measure of the relative reliability of different fields."

### Appendix (printed pp. 33-35)

Four proofs. Read in full.

- **Proof of Lemma.** Three lines. If the `A_j*` are non-empty, (3.1) is a
  valid edit, because any set of values on its left side is included in the
  left side of one of the `e_r` and is therefore an edit failure.
- **Proof of Theorem 1.** By contradiction. Assume values for fields
  1..K-1 satisfying OMEGA_{K-1} for which *every* value of field K violates
  some edit in OMEGA_K. Identify one failed edit per possible value a_K
  (A.1). Note `A_K^r` cannot equal the full set `A_K`, else there would be
  a failed edit in OMEGA_{K-1}. Apply the Lemma with field K as generating
  field to get (A.2); since the union of the `A_K^r` covers `A_K`, (A.2)
  collapses to (A.3), an edit in OMEGA_{K-1} that the chosen values fail —
  contradiction. The proof closes with the load-bearing remark: "the
  validity of the theorem depends on the set of edits being complete with
  respect to essentially new implied edits, but not necessarily all
  possible edits."
- **Proof of Corollary 2.** Reindex so S = {K,...,N}. Then no failed edit
  involves only fields 1..K-1, so those values satisfy OMEGA_{K-1}, and
  Corollary 1 supplies the rest.
- **Proof of Theorem 2.** Constructive descent. For each value of a_N in
  `A_N^p` pick an explicit failed edit; generate on field N via the Lemma
  to get e*, whose N-th code set contains `A_N^p`. Repeat for each value of
  a_{N-1}, generate on field N-1, and so on down to field 1. The resulting
  edit has `A_j^x` containing `A_j^p` for every j, so it is failed by every
  record failing e_p; hence e_p is generable.
- **Proof of Theorem 3.** Writes e_r and e_s as `f >= 0` and `g >= 0`, solves
  both for a_N (possible because a_N^r > 0 and a_N^s < 0) to get
  `a_N >= f'` and `a_N <= g'`, and observes that `g' >= f'` implies every
  a_N fails one of them — so (A.7) is an implied edit, whose coefficients
  (A.8) multiply up to the theorem's formula. The converse half shows that
  if the two coefficients have the same sign, a counterexample record can
  always be constructed that fails the candidate e_t while satisfying both
  e_r and e_s, so no essentially new edit follows.

Six references: Freund & Hartley (1967) least-squares data editing; Naus,
Johnson & Montalvo (1972); Nordbotten (1965); Pritzker, Ogus & Hansen
(1965); Szameitat & Zindler (1965); Yates (1971).

---

## 4. The definitions, exactly as the paper gives them

**Editing** — Section 1: "A. the checking of each field of every survey
record ... to ascertain whether it contains a valid entry; and B. the
checking of entries in certain predetermined combinations of fields to
ascertain whether the entries are consistent with one another."

**An edit** — Section 2, eq. (2.2)-(2.3): a subset of the code space,
defined by a function f connecting per-field code subsets through union and
intersection, which "becomes an edit if, through some prior knowledge, it
is declared a set of unacceptable code combinations, in the sense that a
record a is said to fail the edit specified by f whenever a is in f".

**Normal form of an edit** — eq. (2.6)/(2.7): `INTERSECTION_{i=1..N} A_i* =
F`, padded with `A_i* = A_i` for fields not explicitly involved. "any edit,
whatever its original form, can be broken down into a series of statements
of the form 'a specified combination of code values is not permissible.'"

**Field enters an edit explicitly** — Section 2, note 1: iff `A_i*` is a
proper subset of `A_i`.

**Explicit edits** — Section 2, note 2: the edits initially specified by
subject-matter experts, in normal form.

**Implied edit** — Section 3, Lemma: the edit e* produced by intersecting
the code sets of the contributing edits on every field except the
generating field, and unioning them on the generating field, provided no
resulting set is empty.

**Essentially new implied edit** — Section 3, after the Lemma: an implied
edit in which the generating field's code set `A_i*` equals the *whole*
code set `A_i`, while every contributing edit had a proper subset there. It
"does not involve all the fields explicitly involved in the e_r".

**Complete set of edits (OMEGA)** — Section 3: "The set of explicit
(initially specified) edits, together with the set of all essentially new
implied edits".

**Inconsistent set of edits** — Section 3: a set which "jointly imply that
there are permissible values of a single field which would automatically
cause edit failures, irrespective of the values in the other fields";
equivalently, there is an implied edit of the form `A_i^r = F` with `A_i^r`
a proper subset of the possible values of field i.

**The minimum-change criterion** — Section 1, Criterion 1: "The data in
each record should be made to satisfy all edits by changing the fewest
possible items of data (fields)." Operationalised by Corollary 2 and, as an
algorithm, by Section 5.4: choose the smallest set of columns of the failed
edit matrix that together have at least a 1 in every failed row.

**Imputation** — Section 1, footnote 1: "changing the values in some of its
fields to possible alternatives with a view to insuring that the resultant
data record satisfies all edits."

---

## 5. What this means for siting-atlas

### 5.1 The three conflicting facility dates — a principled procedure

`warehouse/facilities.py:206` takes `min(open_q_index)` across the records
matched to one building. Three pairs disagree by 10, 6 and 3 quarters. Here
is what this paper actually prescribes, worked through, with the one
honest gap stated plainly.

**Step 1. Declare the edit.** In normal form (eq. 2.7), over a merged
entity carrying both sources' date fields:

```
  E_date :  (link_score >= STREET_MATCH)
            INTERSECT (open_q_index_A != open_q_index_B)  =  F
```

That is a legitimate Type B edit — a predetermined combination of fields
declared jointly unacceptable. It is currently declared nowhere.

**Step 2. Error-localise.** Build the failed edit matrix (Sec. 5.4). For
the Hawthorne pair the two records agree on street (after standardisation),
city, state, zip and geography, and disagree only on the opening date. So
E_date is the only failed row, and the smallest set of columns covering it
is the single field `open_q_index`. **Corollary 2 therefore says: change
the date, and change nothing else.** That is already strictly more than
`min()` tells us — `min()` does not record that a field was changed, let
alone which one, and a reader of the panel cannot tell an adjudicated date
from a reported one.

**Step 3. Choose the value — and this is where the paper stops short.**
Corollary 2 asserts that *a* satisfying value exists; Section 4 computes
the admissible set from the edits. Here that set is uninformative: any
value satisfying `open_q_index_A == open_q_index_B` passes, so 2020Q2 and
2017Q4 are equally admissible. The edits do not pin down the value.

**This is the correction we owe our own documentation.**
`docs/data/DATA_QUALITY.md` R2 currently reads "Fellegi-Holt error
localisation — when records conflict, change the minimum number of fields
needed to satisfy the edits ... Here the minimum change is one date per
pair." The first clause is right and the last clause quietly slides from
*which field* to *which value*. Minimum change selects the field. It does
not select the date.

**Step 4. Section 7 supplies what Section 3 does not.** Where the edits
leave a choice, Fellegi and Holt prescribe an **a priori reliability weight
per field** — "we could simply take the set with the lowest product of a
priori weights" — with the worked intuition that "If one field is the
product of a complicated coding operation and the other is a self-coded
response, then ... the simple self-coded response is more likely to be
error-free." For us the weight attaches to the *provenance* of each date,
which is exactly the distinction Fellegi and Holt draw: an OSHA inspection
date is a derived, coded artefact of a regulatory process; a permit or
press record is closer to a direct report. Declare the ranking once, in
`docs/data/FACILITY_PANEL_PROVENANCE.md`, and apply it.

Section 7 also gives the less subjective alternative: "one can edit the
records in one pass ... and determine for each field the proportion of
edits entered by the fields which are failed." With three pairs there is
not enough signal for that, and I would not pretend otherwise.

**Step 5. Where the provenances rank equal, the paper says stop guessing.**
Section 1, option 2: "Corrections of Type 1 and 2, particularly 2, are
certainly worthwhile if feasible: one should, whenever possible, avoid
'manufacturing' data instead of collecting it." Three permit lookups. R2
already proposes exactly this, so R2's *action* is right; only its
justification needed fixing.

**Step 6. Log it.** Section 6.1 items 5, 6 and 7: a per-record log of edits
failed, a per-edit log of records failing it, and the uncorrected data
preserved and cross-tabulated against the corrected data.

**Why `min()` is specifically wrong in this paper's terms.** Three
distinct objections, not one:

1. It is an imputation rule specified independently of the edits, which is
   the exact practice Criterion 2 exists to abolish ("It should not be
   necessary to specify imputation rules; they should derive automatically
   from the edit rules") and which Section 1 blames for corrections whose
   "net impact ... is unforeseeable".
2. It is *directional*. `min()` always resolves toward the earlier date, so
   it is a biased estimator of the opening quarter — biased early, by
   construction, on every conflicting pair. Under a timing model that is
   bias in the outcome, on the order of 170 ZCTA-quarters.
3. It therefore also violates Criterion 3, which asks that imputation
   maintain the frequency distribution of the variable. Systematically
   taking the minimum shifts the opening-date distribution earlier.

### 5.2 Complete-case deletion at `cost/runner.py:166`

Fellegi and Holt's option 5 is our default treatment, and they dispatched
it in 1976, three sentences, no missing-data vocabulary required: "Option 5
would involve an implicit assumption that the statistical inferences are
unaffected by such deletions. This is equivalent to assuming that the
deleted records have the same distribution as the satisfactory records."
That is the MCAR assumption stated before MCAR had a name, and it is a
better citation for our purposes than Little & Rubin because it arrives
attached to the alternative: "If such an assumption must be made it would
seem much more sensible to make it through imputation techniques."

Note the scope. They are not saying never delete; they are saying deletion
carries an assumption, and if you are going to make the assumption anyway,
imputation uses more of the data. Our `rent_index` case is worse than the
one they had in mind, because we can *show* the assumption fails — the
present stratum is 63.6x denser.

### 5.3 The 19-ZCTA false positive has a fix in this paper

`DATA_QUALITY.md` F3 found that the edit `owner_occupied + renter_occupied
== households` fires on 19 ZCTAs that are in the gazetteer but absent from
ACS 2023, where every field is NULL, so the identity is "vacuously unequal
rather than contradicted". Section 2, note 6 is the fix, and it is two
lines of work:

> "We accept a convention that whenever one of the fields of a record
> contains an invalid entry (i.e., one which is not among the set of
> possible values), we consider the record as failing all edits which that
> field enters explicitly."

Combined with note 3(a) — reserve one extra code `c_i` per field for "all
the invalid codes of Field i" and map invalid entries to it at load — the
19 ZCTAs stop being an arithmetic accident and become a declared,
countable state: "fails the ACS presence edit", which is a different
finding from "fails the household identity". Section 5.1 shows the same
trick in the bit-matrix ("All we need do is expand the code set for every
field by the inclusion of an extra code labeled 'Invalid'").

Note 6 also draws the distinction we need for `enabled.fillna(False)` at
`facilities.py:215`: "The code value 'blank' may or may not be among the
set of possible (i.e., permissible) values of a field". "Not covered by any
known catchment" is a permissible blank; "known not to be served" is a
value. Collapsing them is exactly the error the convention prevents.

### 5.4 Should we build the solver? What this paper says about cost

The honest reading is that the *theory* is free and the *machinery* is not,
and they separate cleanly:

- **Free, and we should take it.** The normal form (Sec. 2) is just
  "declare each constraint as a forbidden combination". The consistency
  check (Sec. 3, end; Sec. 5.2) catches self-contradictory edit sets
  "before data processing begins". The invalid-code convention (Sec. 2,
  note 6). The three logs (Sec. 6.1, items 5-7). The a priori reliability
  weights (Sec. 7). None of these requires generating a single implied
  edit.
- **Expensive, and we should not.** Implied-edit generation (Lemma, Thm 2,
  Sec. 5.2) and set-cover error localisation (Sec. 5.4). Theorem 1's
  guarantee *requires* a complete set of edits, and a partially generated
  set gives you a false guarantee rather than a weaker one.

Our edit set is 22 mostly-independent constraints over ~15 numeric fields,
and there is exactly one place in the project where error localisation
would tell us something we cannot work out by inspection — the three
facility pairs, where the minimal cover is a single field and is obvious.
Paying for the solver to answer three questions we can answer on paper is
not a trade this project should make. See `NOTES_winkler_rr99_01.md` §5 for
the cost numbers and the same conclusion reached from the other direction.

### 5.5 A smaller point about ordering

Section 5.1: "as far as editing only is concerned, implied edits need not
be considered — if the initially stated explicit edits all pass, no implied
edit can fail." So a *detection-only* edit gate — which is what R6 proposes
— is complete without any of the expensive machinery. The machinery buys
correction, not detection. That is a cleaner argument for R6 than the one
currently in `DATA_QUALITY.md`.

---

## 6. What I did NOT read or did not understand

- **Nothing was skipped.** All 20 PDF pages: the JSTOR cover, Sections 1-7,
  Tables 1 and 2, Examples 1-3, the full Appendix with all five proofs, and
  the six references.
- **The PDF text layer is badly damaged in places**, and this is the main
  caveat on these notes. Tables 1 and 2 in Section 5.1 are bit matrices
  whose columns have been scrambled by the OCR — the header row and the
  data rows are interleaved out of order in the extracted text. I have
  described what the matrices *are* and how they are read, and I am
  confident of that from the surrounding prose, but **I have not
  reconstructed the exact 0/1 contents of Table 1 and would not trust
  anyone who claimed to from this text layer.** If the bit representation
  ever needs implementing, render PDF pages 12-13 as images first.
- Similarly, the failed-edit-matrix tabulations in Section 5.4 are
  scrambled. The worked example's *conclusion* (minimal set = {Rel. to
  Head, Age}) is stated in prose and is safe; the intermediate matrices I
  have summarised from the prose, not read off the tables.
- **Example 2's edit II** is transcribed in the text layer as both
  "2b >= a + 3c" and "-a + 2b - 3c >= 0", which agree; but the derived
  edits III-V and the bound "c between zero and 5/3" I have taken on the
  authors' word rather than re-deriving. I did re-derive Theorem 3's
  coefficient formula and it is right.
- **Mathematical notation throughout is mangled by the extraction** —
  set-membership symbols render as "C", "E" or nothing, intersections as
  "n" or "(\", subscripts and superscripts are flattened. I have
  reconstructed the mathematics from context and it is internally
  consistent, but the equation numbers (2.1)-(2.7), (3.1), (4.1)-(4.3),
  (A.1)-(A.8) are reliable while the exact glyphs in my transcriptions are
  my reconstruction, not the paper's typography.
- **The forthcoming paper on quantitative data** referred to twice ("A
  subsequent paper by one of the authors deals with quantitative data
  specifically") is not in `../Research/` and I have not chased it. If
  arithmetic edits ever become central, that paper and Sande (1979) are the
  places to go — see `NOTES_winkler_rr99_01.md`.
- **I did not verify the JSTOR page mapping against printed folios on
  every page.** PDF page 2 carries "17" and PDF page 20 carries "35", and
  the intervening headers run in sequence, so the offset of -15 is sound.
