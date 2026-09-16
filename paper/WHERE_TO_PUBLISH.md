# Where to send this, and how to position it

**Caveat before anything else.** Deadlines, page limits and scope statements
change every year, and this was written from knowledge with a cutoff — **check
every venue's current call for papers yourself before committing**. Nothing
below should be treated as a live date. What does not go stale is the
*reasoning* about fit, and that is what this document is for.

---

## The honest problem, stated first

A negative result is harder to place than a positive one. Reviewers at general
venues are trained to ask "what's new?", and "we tried and it didn't work" is
a weak answer to that question — even when it is the correct answer.

**So do not sell the null. Sell the protocol and the measurement.** This paper
has three things a reviewer can say yes to that have nothing to do with the
model failing:

1. **A pre-registration with a verifiable seal.** Hashed before fitting, hash
   recorded in the result artefact, checked by CI. In applied siting work this
   is, as far as we can tell, unprecedented. That is a *methods* contribution.
2. **A counted fact nobody has published**: federal records see 138 of the 488
   US cities with a delivery station. That is not a null. It is a measurement,
   and it is the thing a journalist or a policy reviewer will quote.
3. **A recovered dataset** of 1,904 facilities that did not previously exist in
   machine-readable form.

Any one of those carries a paper. The null is the *finding*, but it should not
be the *pitch*.

---

## Tier 1 — venues that actively want this

These are where acceptance is most likely, because the thing that makes the
paper awkward elsewhere is the thing they exist for.

### 1. NeurIPS "I Can't Believe It's Not Better" (ICBINB) workshop

**The single best fit.** This workshop exists specifically for negative,
surprising and unexpected results, and for papers that explain *why* a
reasonable idea failed. A pre-registered null with a mechanism (publication
grain), a screening rule, and an honest account of what the authors got wrong
is close to their ideal submission.

- Workshop papers are short — typically 4–6 pages — so you would submit a
  compressed version, not this one.
- Non-archival at most workshops, which means **you can submit the full paper
  to a journal or conference afterwards**. That makes it low-risk.
- Check whether the workshop ran in the current cycle; workshop line-ups change
  year to year.

### 2. ACM COMPASS — Computing and Sustainable Societies

Public-interest computing, equity, and the relationship between data and
communities. The framing that fits: *communities negotiate warehouse siting
without the information the operator has, and we measured the size of that
asymmetry.* COMPASS reviewers will care about the visibility gap far more than
about the AUC.

### 3. Data & Policy (Cambridge University Press)

Open-access journal, explicitly for data science that bears on policy. A
journal gives you space — your paper is already 12 pages and would need heavy
cutting for a conference, but not for here. Journals are also more comfortable
with null results than conferences are.

---

## Tier 2 — good fit, more competitive

| Venue | Why it fits | What to lead with |
|---|---|---|
| **ACM FAccT** | The visibility gap is an accountability and transparency finding | 138 of 488; who can and cannot see infrastructure decisions |
| **ACM SIGSPATIAL** (short paper, or a workshop) | Spatial methods, facility location, geographic grain | The grain diagnosis and the dispersion screen |
| **Environment and Planning B: Urban Analytics and City Science** | Urban analytics journal, methodologically open | The full result, with room for the threats section |
| **Transportation Research Board annual meeting** | Freight and last-mile logistics | The cost model and the feasibility-binds-first finding |

---

## Tier 3 — publish the dataset separately

**This is the move most people miss, and it may be the highest-value one.**
The 1,904-facility table is independently useful to people who do not care
about your model at all. It can be its own publication:

- **NeurIPS Datasets & Benchmarks track** — a recognised venue for data
  artefacts, peer-reviewed, archival.
- **Scientific Data** (Nature Portfolio) — data descriptors. Requires the data
  to be deposited in a repository with a DOI; Zenodo satisfies this and takes
  about ten minutes.
- **Journal of Open Source Software (JOSS)** — for the *software*, not the
  research. Short, fast, genuinely peer-reviewed, and a real citation. The
  reproducible-offline pipeline and the OCR toolchain would qualify.

A dataset paper and a findings paper are not competing submissions. They cite
each other.

---

## Always do this first: a preprint

Put it on **arXiv** (`cs.CY` Computers and Society, cross-listed `econ.EM` or
`stat.AP`) the day you are happy with it.

- Establishes the date on the pre-registration claim publicly.
- Costs nothing and blocks nothing — every venue above permits preprints, but
  **verify that for the specific venue**, because a small number of journals
  still do not.
- Gives you a link to put in the repository README, on LinkedIn, and in the
  county outreach email.

**Get a Zenodo DOI for the repository at the same time.** One click from
GitHub, and it makes the dataset citable. A dataset with a DOI gets used; a
dataset in a GitHub folder gets forgotten.

---

## How to position it so it lands

### The title should promise a measurement, not a failure

The current title does this correctly — *"What Open Data Cannot Tell You…"* is
a claim about the world, not an apology. Keep that instinct anywhere you
re-title.

### Lead every abstract with the protocol

Not "we tried to predict siting and could not." Instead: "we pre-registered a
test of whether open data can predict siting, hashed the registration before
fitting, and report the registered outcome." The first framing invites *why
should I read a failure?*. The second invites *how did they do that?*.

### Give reviewers the three quotable facts early

```
  138 of 488   cities visible in federal records
  0 of 7       held-out years beating a households baseline
  $1.08        median cost to deliver one parcel, from public data alone
```

A reviewer who remembers one number will remember the first one.

### Make the artefact impossible to ignore

Put the verification command in the paper itself:

```
md5sum docs/PREREG_METRO_MODEL.md
make reproduce          # offline, no API keys
```

Most papers claim reproducibility. Very few let a reviewer test the claim in
two commands during review. Say so explicitly in the submission — some venues
have a reproducibility badge track, and this would qualify.

### Own the mistakes in the paper, not in the rebuttal

The paper already does this: the Daganzo citation error you found in your own
bibliography, the fabricated figure caught in your own audit, the correction
that runs against your own hypothesis. **Keep all of it.** A reviewer who sees
you disclose an error you could have hidden extends trust to everything else.
A reviewer who finds an undisclosed error stops reading.

---

## What to cut for a 6–8 page conference

The paper is ~12 pages and ~8,600 words. In order of what costs least:

1. **§V-E, the three retired programmes** (~1 page). They support the argument
   but none is load-bearing.
2. **The gravity material** throughout (~0.5 page). It is a negative inside a
   negative.
3. **Compress §VII Threats from eleven subsections to five or six.** Keep: one
   operator; the 29-decision leakage limit; the dispersion finding being
   descriptive; the cost model's unvalidatable constant; the errata. Merge the
   engineering caveats into one paragraph.
4. **Cut the abstract from 386 words to ~200.** It is currently over the norm
   for almost every venue and reads as three abstracts stacked.

Do **not** cut, whatever the page pressure: the pre-registration mechanics, the
Daganzo disclosure, the Simpson's-paradox stratification, or the statement
that the covariate mechanism was never testable on this panel. Those four are
why the paper is worth reading.

---

## Red flags that will get it rejected, and how to avoid each

| Risk | Reviewer's objection | Your answer, already in the paper |
|---|---|---|
| "This is just a failed project" | negative results are cheap | It was pre-registered and hashed; the hash is checkable |
| "One operator, one country" | no external validity | Stated in the first Threats subsection, and never over-claimed |
| "AUC 0.73 sounds fine" | the null is overstated | Stratification: 0.73 pooled is higher than every tier; the baseline gets 0.89 |
| "Maybe your model is just bad" | a stronger model would work | The GBM benchmark, and `vintage_relaxed` losing even when allowed to cheat |
| "The cost model isn't validated" | unsupported numbers | Conceded explicitly; five scenarios reported; eight parameters flagged as unsourced |

The fourth row is the one to prepare hardest for, and the answer is the
strongest thing in the paper: **the model loses to the baseline even when it
is permitted to see data published after the year it is predicting.** That is
not a weak model. That is a ceiling.

---

## A suggested sequence

1. arXiv preprint + Zenodo DOI for the repo.
2. Compress to 6 pages, submit to **ICBINB** — low risk, non-archival, and
   feedback from reviewers who are sympathetic to the form.
3. In parallel, prepare the dataset descriptor for **Scientific Data** or the
   **NeurIPS Datasets & Benchmarks** track. Different artefact, different
   reviewers, no conflict.
4. Take the workshop feedback into a full submission to **COMPASS** or
   **Data & Policy**.

That sequence gets something published early, keeps the strong version
unblocked, and gets the dataset cited independently of whether the findings
paper lands.
