# Handbook Part 7 — Engineering

**How three people on laptops ship this in nine weeks. The pipeline, the one
component that would have broken it, and the habits that keep a shared project
from rotting.**

---

## 7.1 The shape of the problem

Start with the honest sizing, because it determines every other decision.

```
   WHAT WE MODEL ON                        WHAT PASSES THROUGH
   -----------------------------------     ----------------------------------
   ZCTA-quarter panel  1,081,312 rows      OpenStreetMap extracts   ~12 GB
                       14 MB               Routing artifacts        2-5 GB/metro
   Warehouse           300-500 MB          EPA EJScreen             1-2 GB
   OD drive times      10 MB               TIGER/Line raw           600 MB
   Facility panel      < 1 MB              Everything else          < 500 MB
```

The left column is measured, not planned. The panel is 33,791 ZCTAs x 32
quarters x **50 columns** over 2018-2025 (measured from
`data/processed/panel.parquet` on 2026-09-14; an earlier draft said 44 columns
and that is stale). An earlier sizing in this handbook said 811,200 rows and
260 MB for a ZCTA-*week* panel over ten metros. The built thing is both wider in
coverage and eighteen times smaller on disk, because quarterly demographics
compress far better than a weekly grid of the same slowly-moving numbers would.

**Two conclusions follow immediately.**

1. **Nothing here is a distributed-computing problem.** The analytical data fits
   in memory on a decade-old laptop. If anyone proposes Spark, the answer is no,
   and the reason is that it would add operational complexity to solve a problem
   we do not have.
2. **The only heavy component is road-network preprocessing**, and §7.4 removes
   it from the critical path entirely.

> **Why this framing matters beyond the engineering.** A project that claims to
> be "big data" and turns out to be 14 MB has an unrecoverable credibility
> problem. A project that says "deliberately small, because the hard part is
> identification" and then backs it with an uncertainty analysis it actually
> ran has the opposite.

> **A claim withdrawn.** That sentence used to end "...and *then* shows a
> 24-billion-draw uncertainty design has the opposite." **There is no
> 24-billion-draw anything.** 24,130,000,000 is
> `compute.draws_total` in `outputs/metrics/scope.json` — a *specification*
> number that was never executed. What was executed is a **500-draw** Monte
> Carlo over the portfolio parameters, seed 20260914, 500 of 500 draws
> successful (`outputs/metrics/montecarlo_report.json`,
> `outputs/tables/montecarlo_draws.parquet`, 500 rows x 28 columns). There was
> never a 10,000-draw NPV Monte Carlo either. Citing a spec number as a
> delivered compute figure is the single easiest thing for an examiner to
> falsify — it is one `ls` away. Corrected 2026-09-14.

---

## 7.2 The five-layer pipeline

Every stage has one job, one owner, and one definition of done.

```
  ┌──────────────────────────────────────────────────────────────────┐
  │  L0  ACQUIRE       content-addressed cache, write-once           │
  │      data/raw/<source>/<sha256>.<ext>  +  manifest.jsonl         │
  │      a re-run costs zero network                                 │
  └──────────────────────────────────────────────────────────────────┘
                                 ↓
  ┌──────────────────────────────────────────────────────────────────┐
  │  L1  NORMALISE     one typed parquet per source                  │
  │      geometry simplified here, once                              │
  │      CSV and JSON never appear downstream of this line           │
  └──────────────────────────────────────────────────────────────────┘
                                 ↓
  ┌──────────────────────────────────────────────────────────────────┐
  │  L2  CONFORM       dbt Core -> DuckDB star schema                │
  │      staging/ -> marts/  +  data contracts                       │
  └──────────────────────────────────────────────────────────────────┘
                                 ↓
  ┌──────────────────────────────────────────────────────────────────┐
  │  L3  FEATURE       the 1.08M-row panel. One parquet.             │
  │      This is what every model reads.                             │
  └──────────────────────────────────────────────────────────────────┘
                                 ↓
  ┌──────────────────────────────────────────────────────────────────┐
  │  L4  MODEL/SERVE   hazard, SCM, cost, optimiser, agent, app      │
  │      reads L3 only. No model ever touches raw data.              │
  └──────────────────────────────────────────────────────────────────┘
```

### L4, annotated honestly

That box lists six things. They are not in the same state, and the difference
matters more than the diagram does. Here is the same layer with the status
written in:

```
  +------------------------------------------------------------------+
  |  L4  MODEL / SERVE                                               |
  |                                                                  |
  |    cost        WORKS   Daganzo over a solved depot network       |
  |                        2,333 priced ZCTAs across 10 metros,      |
  |                        median $1.0830/parcel                     |
  |                        (p10 $0.9778, p90 $1.4180)                |
  |                        run 20260914-002418-0623                  |
  |    optimiser   WORKS   greedy + pairwise swap, gap reported      |
  |                        against a computed bound. At a $2bn       |
  |                        budget it activates 282 and spends        |
  |                        $1.128bn = 56.4%, so it DECLINES about    |
  |                        44%. Capacity is 500, so capacity is NOT  |
  |                        binding. run 20260914-002431-7419         |
  |    agent       WORKS   six gates against the real 33,791-ZCTA    |
  |                        warehouse, audit record per invocation.   |
  |                        Caveat: gate 6 refits the RETIRED hazard  |
  |                        model. See HANDBOOK_06_AGENT.md 6.7.0     |
  |    app         WORKS   streamlit over the same chart functions   |
  |                        the figure builder uses                   |
  |    montecarlo  WORKS   500 of 500 draws, seed 20260914, over     |
  |                        the portfolio parameters. NOT a           |
  |                        confidence interval, and every band is a  |
  |                        FLOOR. See Sec. 7.6.1                     |
  |                                                                  |
  |    choice      FITTED, AND THE RESULT IS NEGATIVE.               |
  |                        Conditional ZCTA choice, national frame,  |
  |                        94 decisions, 56 train / 38 held out, 3   |
  |                        free parameters, converged. McFadden      |
  |                        rho-squared 0.19691 in sample.            |
  |                        ON THE 38 HELD-OUT DECISIONS A RAW CBP    |
  |                        WAREHOUSING COUNT (NAICS 493, nothing     |
  |                        fitted from it) MATCHES IT:               |
  |                          top-1   7/38 vs 8/38                    |
  |                          top-5  16/38 vs 16/38  (tie)            |
  |                          top-10 19/38 vs 20/38                   |
  |                        Two of three parameters sit at the        |
  |                        boundary at ~3e-16. Intervals landed      |
  |                        2026-09-14 and all cover the null of      |
  |                        beta = 1 (households is the numeraire).   |
  |                        outputs/metrics/choice_report.json        |
  |                                                                  |
  |    hazard      RETIRED / SUPERSEDED, and it FAILED.              |
  |                        Built, fitted on real data, negative      |
  |                        result. AUC 0.6894 vs a null of 0.5000;   |
  |                        calibration 170x WORSE than the null;     |
  |                        negative Brier skill on both hold-outs.   |
  |                        Kept as teaching, not as a result.        |
  |                        See HANDBOOK_04_MODELS.md                 |
  |                                                                  |
  |    SCM         DOES NOT EXIST.  Synthetic control is the         |
  |                        project's second estimand and not one     |
  |                        line of it has been written. There is no  |
  |                        scm module in src/siting_atlas/.          |
  |                        See HANDBOOK_03_CAUSAL.md Sec. 3.0        |
  +------------------------------------------------------------------+
```

> **Three claims corrected in that box, all measured 2026-09-14.** (1) The cost
> median was quoted as **$1.0875/parcel**; the current artefact
> `outputs/metrics/cost_report.json` says **1.082994**, quoted as **$1.0830**.
> Any $1.0875, $1.0874 or $1.09 in this pack is stale. (2) The optimiser was
> described as spending "roughly two thirds" of the budget; it spends
> **$1.128bn of $2bn, which is 56.4%**, so the honest verb is that it declines
> about **44%**. (3) The `hazard` row was the only model row, which presented a
> failed and retired model as the project's siting result; a `choice` row now
> sits beside it.

> **A fourth correction, 2026-09-14, and this one was an error rather than a
> staleness.** The `choice` row said the raw CBP count **BEATS IT**. It does
> not; it **matches** it. That verb came off a single seeded 56/38 split — the
> three lines of top-k printed in the box. Re-split the same 94 decisions
> fifty times and the raw count leads by **0.36 hits out of 38 (paired sd
> 1.14)** while losing 11 of the 50 outright
> (`outputs/metrics/gbm_benchmark.json`). A third of a decision is not a win
> for the count and not a loss for the model; the old wording promoted noise
> to a finding. The per-split numbers in the box are still right for their
> seed, and the row's verdict — **FITTED, AND THE RESULT IS NEGATIVE** — is
> exactly as negative as it was: three fitted parameters buy no ranking
> improvement over a free download.

**The components that never needed the facility panel are the ones that
survived.** Cost, the optimiser, the agent, the app and the Monte Carlo all run.
The two that needed a large sample of dated, independent siting decisions are
the two in trouble: the hazard model got one that was not independent and
failed, the choice model got one that was independent and too small to improve
on a raw count, and the estimand downstream of both was never started.

> **Why an engineering chapter has to say this.** An architecture diagram is a
> claim about what exists. Leaving "SCM" in a box alongside things that run
> is not a diagramming shortcut, it is a false statement about the system - and
> it is exactly the kind of thing a reviewer checks by running `ls src/`. Label
> the boxes or delete them.

### The rule that makes the layering worth having

**Nothing above L3 knows where the bytes came from.**

That is what makes Volume II a data swap rather than a rewrite. Point L0–L2 at
data-centre siting instead of delivery stations and the entire model layer is
unchanged. It is also what makes the scale answer credible: if the data grew
100×, L0–L2 move to object storage and a distributed engine, and L3–L4 do not
notice.

---

## 7.3 Content-addressed caching

**The rule:** every network fetch is keyed by the hash of its request and
written once.

```
   data/raw/census_acs/9f2c1a…e7.json
   data/raw/manifest.jsonl        {source, url, params, sha256, fetched_at,
                                   bytes, content_type}
```

> **Worked example of why.** You fetch ACS on Tuesday. On Thursday you add a
> feature and re-run the pipeline.
>
> - **Without a cache:** you re-hit the API. Twenty minutes. If they rate-limit
>   you, you are blocked, and you cannot work on a plane.
> - **With a cache:** the same request hashes to the same key, so it is a local
>   file read. 0.2 seconds, and it works offline.
>
> You will run this pipeline several hundred times over nine weeks. Make re-runs
> free on day one, not in week six.

**The manifest is also the reproducibility story.** It records exactly which
bytes produced which result. A reviewer can re-download from the recorded URLs
and verify the hashes.

---

## 7.4 The routing decision — the one that mattered

### What would have gone wrong

OSRM does not read a map, it **preprocesses** one, and preprocessing scales
badly:

```
   metro bbox PBF    200 MB   ->  extract  ->  2-5 GB of artifacts
   California PBF    1.2 GB   ->  extract  ->  15-25 GB, slow on 16 GB RAM
   full US PBF        12 GB   ->  extract  ->  needs 64-128 GB RAM
```

Serving ten metros simultaneously means roughly **30 GB of artifacts** plus the
source files, and on 8 GB of RAM the extract step for a large metro simply
fails. This was the single biggest infrastructure risk in the project.

### The insight

> **We never needed a routing service. We needed a table of drive times.**

The cost model uses `d_stem(i)` — drive time from the nearest node to each
ZCTA. That is a finite, precomputable set: roughly 800,000 within-metro
origin–destination pairs, which stores as a **10 MB parquet file**.

```
   FOR EACH METRO, ONE AT A TIME:
     1. download the metro bbox extract         (~200 MB)
     2. preprocess
     3. query the full OD table
     4. write od_<metro>.parquet                (~1 MB)
     5. DELETE the extract and every artifact   <-- the step that matters
     6. next metro

   PEAK DISK   one metro (~5 GB), not ten (~30 GB)
   SHIPPED     ten parquets = ~10 MB, no routing engine anywhere
```

### What this buys beyond disk

- No Docker container in the deployed app
- No cold-start latency on the public URL
- Nothing routing-related that can fail during a live demo
- The app is a single process reading parquet files

### The fallback, in case even that is too much

Daganzo's law is already a continuous approximation, so exact routing is
precision in the wrong place. Approximate road distance as great-circle ×
circuity factor (*k* ≈ 1.35), calibrate *k* on one metro against routed truth,
report the residual, apply to the rest.

**If the residual is large you have a finding; if it is small you saved two
weeks.** Decide which path in week zero — not on day three of week three.

---

## 7.5 Data contracts

A contract is an assertion that fails the build. Not a warning, not a log line.

| Contract | Why |
|---|---|
| ZCTA count within tolerance of the pinned vintage | **Catches vintage mixing, which is otherwise silent** |
| Row count drop > 5% between runs | Catches a partial fetch or a broken join |
| Null rate per column below a documented threshold | Catches upstream schema drift |
| Referential integrity on every foreign key | Catches orphaned facts |
| No duplicate `(zcta_id, date_id)` | Catches a fan-out join. **NOT ENFORCED TODAY** - see the xfail in §7.6 |
| Geometry validity and CRS | Catches a projection mistake before it reaches a map |

> **Why vintage mixing is the dangerous one.** It throws no error. A ZCTA that
> split between vintages shows a sudden 50% "population drop", the model reads a
> demand collapse, and everything downstream is plausible and wrong. That is why
> the ZCTA count is enforced rather than assumed.

---

## 7.6 Reproducibility

The claim is that a stranger can rebuild this. That has to be true literally.

```
  reproducibility/
    seeds.toml            every stochastic step reads its seed from here
    environment/
      requirements.lock   pinned with hashes
      python-version
    MANIFEST.md           what was run, when, on what commit
```

Plus:

- **One `make` target per stage.** `make acquire`, `make features`, `make model`,
  `make app`. Anyone can rebuild anything without reading code.
- **`make all` from a cold clone** is the acceptance test, and it should run
  offline against a warm cache.
- **Never commit data.** `data/` is gitignored; everything is re-derivable from
  the manifest. The repo stays under 50 MB and clones in seconds.
- **Someone outside the team runs it** before submission. This always finds
  something — usually an undocumented environment variable or a path that
  only exists on one laptop.

### Version control, which this section used not to mention at all

**The repository is under git, with 23 commits at the time of writing**
(`git rev-list --count HEAD`, 2026-09-14 08:13 UTC, HEAD `b29071e`). Any claim
anywhere that this project is not under version control is false.

> **Why the omission mattered.** A section whose whole claim is "a stranger can
> rebuild this" was silent on the one mechanism that makes rebuilding a
> specific state possible. A `MANIFEST.md` recording "what was run, on what
> commit" is meaningless without commits to refer to. Stating the status is
> also what lets a reviewer check the rest of it.

**And keep "under version control" and "committed" apart, because they came
apart during this very session.** For several hours the whole choice-inference
module (`models/choice_inference.py`, `choice_sandwich.py`,
`choice_bootstrap.py`, `tests/unit/test_choice_inference.py`) sat on disk,
changed the published `choice_report.json`, and was untracked by git. It was
committed as `b29071e` on 2026-09-14. Anyone quoting a result during that
window would have been quoting a number no commit could reproduce. Before you
cite a figure, check that the artefact that produced it is committed — the
repository being under git does not by itself make any particular result
reproducible.

### The test suite, and why this section refuses to give you a number to memorise

**Do not memorise a passing count from this section.** Run `pytest` and quote
what you get, with the time you got it. The reason for that instruction is the
subject of the rest of this section, and it is a better viva answer than the
count would have been.

Measured on **2026-09-14 at 08:13 UTC**, at commit `b29071e`:

```
   pytest        648 passed, 2 xfailed      (650 collected)
   ruff          clean on src/ and tests/
```

> **A claim corrected, for the third time, which is itself the finding.** This
> section quoted **483 passed, 2 xfailed** and carried a paragraph noting that
> an earlier draft's "426 tests" was stale everywhere it appeared. 483 was
> stale too. Three generations of the same defect in the same paragraph is
> enough evidence to stop treating it as a transcription slip: **a hard-coded
> count in prose has no owner and no test, so it rots silently while everything
> around it is verified.** The durable fix is to emit the count into a build
> artefact and reference the artefact, exactly as §7.10 argues for figure
> layout. **That fix has not been made**, and the timestamp above is a
> workaround for it, not a solution.

> **And here is the evidence that the workaround is necessary, measured the
> same morning.** Over roughly two hours on 2026-09-14 this suite was observed
> at, in order: 638 passed / 2 xfailed on the committed tree; 648 passed /
> 2 xfailed once an untracked inference module was on disk; 645 passed /
> 3 failed / 2 xfailed; 646 passed / 2 failed / 2 xfailed; and finally 648
> passed / 2 xfailed once the work was committed. Every one of those was a
> correct measurement of a different tree. A defence document that had frozen
> any single one of them would have been wrong within the hour.

**What the red phase was, since it is worth knowing and it will recur.** The
failures were in `tests/unit/test_batch_candidates.py`, which pinned assertions
to a **three-batch** hand-labelling programme (210 rows, 85 delivery stations,
4 UNKNOWN answers) after batches 4, 5 and 6 had taken it to **362 rows, 135
delivery stations, 8 UNKNOWN** — see `HANDBOOK_02_DATA.md` Sec. 2.2.10. The
tests were stale, not the code: the production numbers were right throughout.
They have since been updated and the suite is green.

> **Do not sand that episode out of the story.** The same defect — a literal
> count frozen in one place while the world it describes moves — appeared in
> this handbook's prose *and* in a test file *and* in a worklist de-duplication
> step (Sec. 2.2.10), within one project. That is a pattern, not three
> coincidences, and the pattern is the finding worth taking to a viva.

> **What the number does and does not prove, because someone will push on it.**
> A passing suite is evidence the *engineering* is sound: the pipeline runs,
> the contracts fire, the gates execute against the real warehouse, the
> optimiser solves. It is **no evidence at all** that the science is sound. The
> hazard model has tests and it passes them; what it fails is the world. A test
> asserts that the code does what you told it to. Nothing in a test suite can
> tell you that what you told it to do was the right thing to do.
>
> Being able to draw that line is worth more in a viva than the count is. The
> project is a demonstration of it, though a messier one than an earlier draft
> claimed: **the engineering mostly works and the science does not**, and both
> statements are backed by artefacts. "Mostly" is doing real work in that
> sentence — the suite was red twice this morning on stale assertions, the
> panel's grain is enforced only by luck (below), and `optimize/objective.py`
> carries a unit-of-analysis bug in a component this chapter labels WORKS
> (§7.11).

### The two xfails, and why they are the most useful two tests in the suite

An expected failure is a test that asserts a known, documented gap. It runs, it
fails, and the suite records that as *expected* rather than green. That is the
right way to hold an open defect: it stays visible in every run, and because
both are marked `strict=True`, the suite turns **red** the day someone
accidentally fixes one without updating the marker.

| xfail | The defect it pins |
|---|---|
| `test_zero_households_does_not_produce_an_infinite_cost` | A ZCTA with zero households gives stop density 0, so `k/sqrt(0)` is infinite and `cost_per_parcel` is `inf`. `cost.runner` filters `households > 0` before calling `evaluate()`, so the shipped pipeline is fine — but any *other* caller (a sensitivity sweep, a notebook, the optimiser) gets `inf` with no warning. The guard belongs in `stop_density()`, not in one caller |
| `test_a_duplicate_county_year_in_permits_does_not_fan_out_the_panel` | **Nothing asserts the panel's grain.** A duplicate `(county_geoid, year)` in building permits, or a county listed twice in the CBSA crosswalk, silently multiplies every ZCTA row in that county. `ingest.normalise` de-duplicates both today, so the shipped panel is correct **by luck rather than by contract** |

> **Read the second one against §7.5.** The data-contract table below lists "no
> duplicate `(zcta_id, date_id)`" as a contract that catches a fan-out join.
> **That contract is not enforced**, and this xfail is the proof. The section
> describes the contract regime as designed; one row of it is aspirational. The
> fix is a single assertion after the panel is built - `COUNT(*) =
> COUNT(DISTINCT (zcta, date_id))` - and until it lands, read that row as a
> plan.
>
> **Both xfails share a shape worth naming: "correct by accident".** In each
> case the shipped output is right, and it is right because of something a
> caller happens to do rather than because of anything the component guarantees.
> A silent upstream change breaks either one with no error. That is the same
> class of bug as vintage mixing (§7.5) and it is the reason the xfails were
> written as failing tests instead of as TODO comments nobody reads.

### 7.6.1 The Monte Carlo — it ran, and every band it reports is a floor

**It ran.** Any text in this pack or elsewhere calling the Monte Carlo
specified, blocked, backlogged, illustrative or not-yet-run is false.

```
   draws            500 attempted, 500 succeeded, 0 failed
   seed             20260914
   artefacts        outputs/metrics/montecarlo_report.json
                    outputs/tables/montecarlo_draws.parquet  500 x 28
   -------------------------------------------------------------------
                          p10       p50       p90     min     max
   activations n          152     264.5       306      82     385
   capital $bn          0.608     1.058     1.224   0.328   1.540
   breakeven margin    1.0892    1.3682    1.7259
   median $/parcel     0.8368    1.1224    1.4836
```

**Four things to say about it, in this order.**

**1. It is not a confidence interval, and the artefact says so itself.** The
`interpretation` field reads: *"NOT a confidence interval. Every range is from
`docs/data/PARAMETERS.md` and was chosen by this project; eight of the
constants have no external source. This measures how far the answer moves
across the range we consider plausible, and it propagates our priors rather
than the world's."* Quote that, do not paraphrase it into something friendlier.

**2. Every band is a FLOOR, because of an oversight.**
`parcels_per_depot_per_day` **was not sampled**. It is fixed at 40,000 in the
cost parameters and it does not appear as a column in
`montecarlo_draws.parquet` — verified 2026-09-14. It is one of the parameters
the answer is most sensitive to, and holding it fixed can only narrow the
spread. So the true ranges are *at least* this wide and possibly much wider.
This was an oversight, not a modelling choice; report it as one.

**3. The headline drift was real, and the parameters did not cause it.** The
published activation count has been quoted at 282, 317 and 330 in different
places. Against the simulated distribution:

```
   282  sits at the 67th percentile   INSIDE the band
   317  sits at the 95th percentile   outside
   330  sits at the 97th percentile   OUTSIDE
```

Only 282 is a comfortable draw from the project's own parameter ranges, and 282
is what the current run produces. So parameter uncertainty does not explain
the older numbers. **Depot placement does — and depot placement is not
classified as a parameter, so the Monte Carlo cannot see it.** That is the
useful finding here: a sensitivity analysis is blind to every choice you did
not put in the parameter list, and the thing that actually moved the headline
was outside it.

**4. The capital figure carries no independent information.** `capital_usd` is
**exactly $4m x n in all 500 draws** (checked: the equality holds on every
row). So the three published capital figures — $1.128bn, $1.268bn, $1.320bn —
are just 282, 317 and 330 restated in dollars. Presenting them as a separate
line of evidence would be double-counting one number.

**The dominant driver of `n` is `cannibalisation_peak`**, reported at 44.3% of
the variance. A crude squared-correlation split over the draws table puts it
higher still, near 53%; the decomposition method changes the share but not the
ranking, and no other parameter is close. Given that `cannibalisation_peak` is
a number somebody typed with no standard error behind it
(`HANDBOOK_03_CAUSAL.md` Sec. 3.0), the single largest source of spread in the
portfolio result is an unestimated assumption.

> **A claim withdrawn.** Earlier text in this pack referred to a 24-billion-draw
> uncertainty design and, elsewhere, to a 10,000-draw NPV Monte Carlo.
> **Neither was ever executed.** See the note in Sec. 7.1.

---

## 7.7 Ten habits that keep this on a laptop

1. **Parquet everywhere after L1.** Roughly 5× smaller, typed, and column-pruned
   reads mean you load three columns instead of forty.
2. **Delete routing artifacts immediately** (§7.4). Non-negotiable.
3. **Develop on one metro, 200 ZCTAs.** Get the pipeline green end to end, then
   scale. A 30-second loop beats a 20-minute loop and you will run it 200 times.
4. **Cache every network call** (§7.3).
5. **Push aggregation into DuckDB.** `SELECT … GROUP BY` over a parquet file
   beats loading it into pandas, and DuckDB spills to disk when it needs to.
6. **Simplify geometry once, at L1.** Full TIGER polygons are ~600 MB and you are
   drawing them at metro zoom; 10 m tolerance gets you ~100 MB and nobody can
   tell.
7. **Pin everything**, including the random seeds. "Works on my machine" is a
   graded failure in a reproducibility project.
8. **Size the Monte Carlo to the question, and say what you ran.** The spec in
   `scope.json` names 24,130,000,000 draws; what was executed is **500**
   (Sec. 7.6.1), and 500 is enough to show the bands are wide. If you ever do
   need the spec figure, vectorise and chunk it — a Python loop will not
   finish — but do not quote a draw count you have not run.
9. **Fail loudly on contracts** (§7.5). Silent data loss is the bug you find in
   week eight.
10. **Log what a run actually did** — commit hash, seed, row counts, timings
    — to a machine-readable file, not to stdout.

---

## 7.8 Hardware, and free compute

| Setup | Verdict |
|---|---|
| **16 GB RAM, 256 GB SSD** | ✅ Sufficient with per-metro routing and delete-as-you-go |
| 8 GB RAM | ⚠️ Works **only** with the circuity fallback (§7.4) |
| 32 GB RAM | Comfortable; still no reason to process full-US OSM |
| GPU | ❌ Not needed anywhere |

| Job | Where | Cost |
|---|---|---|
| Routing preprocessing, if kept | Free notebook tier (~12 GB RAM, ~100 GB disk) | $0 |
| Scheduled ingest, contract checks | CI free tier (2,000 min/month) | $0 |
| App hosting | Free tier | $0 |
| Warehouse | DuckDB, one local file | $0 |
| Dataset hosting | Free dataset host | $0 |

**Total compute cost: $0.** The entire budget is language-model inference.

---

## 7.9 Ownership — stage, not just module

Assigning modules without assigning stages is how a shared pipeline becomes
nobody's responsibility.

| Stage | Owner | Definition of done |
|---|---|---|
| L0 acquire + cache + manifest | P2 | `make acquire` runs offline on a warm cache |
| L1 normalise to parquet | P2 | Every source typed, documented, contract-tested |
| L2 dbt → DuckDB | P1 | `dbt build` green; contracts enforced |
| L3 feature panel | P1 | One versioned parquet, 1,081,312 rows |
| L4 models | P1 | Backtest reproducible from the manifest |
| OD matrix extraction | P2 | Parquets committed; artifacts deleted |
| App + figures | P3 | Loads under 5 s; reads L3/L4 only |
| CI, contracts, reproducibility | P2 | A red build blocks merge |

---

## 7.10 The build toolchain

The documentation and figures are themselves built and validated, on the same
principle as the data pipeline: **if it can be checked automatically, it is.**

```
  tools/figures/     matplotlib figure toolkit
    common.py          palette, auto-fitting box(), edge-anchored link()
    build_all.py       builds all figures, reports any text overflow

  tools/proposal/    Word builder
    docx_kit.py        styles, tables, callouts, figure embedding
    build_v4.py        assembles the proposal

  tools/deck/        PowerPoint builder
    pptx_kit.py        slide primitives with auto-fitting text
    textfit.py         glyph-accurate measurement, shared with the linter
    check_layout.py    coordinate validator (3 geometric rules)

  tools/docs/
    md_to_txt.py       Markdown -> plain ASCII with real ASCII tables

  scripts/build_all.sh   builds everything, validates everything
```

Two details worth copying into your own work:

**Text cannot overflow a box, by construction.** Both the figure toolkit and the
slide toolkit measure rendered glyph extents and shrink the font until it fits.
Eyeballing fourteen figures and twenty-six slides does not catch this; measuring
does. The first validated run of the deck found **21 real defects** that visual
review had missed.

**The builder and the linter share the measurement code.** `textfit.py` is used
by the thing that lays out text and by the thing that verifies it, so a passing
build cannot disagree with a passing check.

---

## 7.11 Risk register

```
  +--------------------------------------------------------------------+
  |  SEVERAL ROWS OF THIS REGISTER HAVE ALREADY FIRED, AND THE REST    |
  |  OF THE OPEN DEFECTS WERE NEVER ON IT AT ALL.                      |
  |  "Facility open dates wrong" was logged as High / High. It         |
  |  happened, the mitigation was insufficient, and it cost the        |
  |  project its first headline model.                                 |
  |  The five rows below it in bold were NOT anticipated by any        |
  |  register; they were found by measurement afterwards. That is      |
  |  worth admitting: a register is only as good as the failure        |
  |  modes you thought of in advance, and this one missed a            |
  |  unit-of-analysis bug, an ungeocoded target table and a listwise   |
  |  deletion that drops 90-odd percent of one covariate.              |
  |  A risk register that is never updated with outcomes is a wish     |
  |  list; updating it is what makes the other rows credible.          |
  +--------------------------------------------------------------------+
```

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Routing preprocessing defeats a laptop | High | High | §7.4 per-metro + delete; circuity fallback |
| **Facility open dates wrong** | **MATERIALISED** | **High**, it is the target | See below |
| **Unit-of-analysis error repeated in a second component** | **MATERIALISED** | **High** | **None.** `optimize/objective.py` prices an activation three inconsistent ways — per ZCTA at `:81-83`, per facility at `:164`, per facility-with-catchment at `:158`. About a **2.74x capital overcharge**. It is the *same* class of error that killed the hazard model, in a component that is otherwise marked WORKS |
| **No facility is geocoded** | **MATERIALISED** | **High** | **None.** 0 of 693 expanded rows, 0 of 104 national rows and 0 of 43 pilot rows carry a latitude or longitude; every distance falls back to a ZCTA centroid. *(Count updated 2026-09-15 for the expanded facility file.)* |
| **589 of 693 panel rows cannot be reproduced from the repository** | **MATERIALISED 2026-09-15** | **Critical** | **None yet.** The industry PDF behind the OCR extraction is an 11 MB file outside the tree, and the archived file with a similar name is a different document (`docs/AUDIT_2026_09_14.md` §1.1). Three independent validations of the extracted rows exist — OSHA cross-check at 94.7%, a plausibility screen, and an OCR-state-vs-crosswalk check at 99.67% — but a validation is not a provenance. The fix is to commit the source, or to publish the intermediate OCR text with its hash |
| **The audit and several research notes are untracked** | **MATERIALISED 2026-09-15** | **Medium** | **None yet, and it is a five-minute job.** `docs/AUDIT_2026_09_14.md`, `docs/data/FIGURES.md`, `docs/data/ARTEFACTS.md` and several `docs/research/NOTES_*.md` are on disk and not under version control, while the code fixes they describe *are* tracked. A clean clone therefore contains some of the retracted material and not all of the retractions |
| **39 of 133 source modules have no test importing them** | **MATERIALISED** | **Medium** | **None yet.** 20 of the 39 are the two-day sprint, and `models/choice_runner.py` — which writes the headline `choice_report.json` — is among them (`docs/AUDIT_2026_09_14.md` §2.2). The suite passes (796 pass, 2 xfail on the last reported run); passing is not coverage |
| **CBP lag guard is nominal** | **MATERIALISED** | **High** | **None.** The guard keys on `open_year`, which on all 100 loaded national rows is the earliest OSHA inspection quarter, not an opening. Measured lags of 4/13/57/69/345 months mean the margin is zero or negative. The exposed covariate is the one that matches the whole fitted model on its own |
| **Line haul understated where demand is bunched** | **MATERIALISED** | Medium, and **directional** | **None.** 42% of depots exceed 40,000 parcels/day, so line haul is a **lower bound** and cost is understated exactly at the top of the published ranking. A systematic bias, not a symmetric error |
| **`rent_index` listwise-deleted** | **MATERIALISED** | **High** | **None.** Missing in at least one quarter for **94.3% of ZCTAs**; 88.8% of *rows* are null; 80.5% of ZCTAs have no value in any quarter. Name the denominator. Still dropped at `cost/runner.py:166`. On the 94.3% split the complete stratum has 63.6x the median household density of the incomplete one, so the deletion is a directional bias |
| ZCTA vintage mixing | Medium | **High** (silent) | Pinned vintage + enforced contract |
| Team blocked on one person's laptop | Medium | High | Everything in CI; nothing lives only locally |
| Scope creep re-adds full-US routing | Low | High | Written into an ADR so it is a decision, not a preference |
| dbt/DuckDB spatial friction | Medium | Low | Geometry work in Python at L1; keep SQL non-spatial |

> **The row to lead with if you are asked "what is still broken?"** The
> `objective.py` one. Not because it is the largest number, but because of what
> it means: the project diagnosed a unit-of-analysis error, retired a model
> over it, wrote three handbook sections about it — and the same error was
> sitting in the optimiser the whole time, in a component the architecture
> diagram labels WORKS. Finding a bug once does not inoculate a codebase
> against it. The honest reading is that the diagnosis was applied to the
> component that failed loudly and never swept across the ones that did not.

### The materialised risk, written up properly

The planned mitigation was *"verify 100, publish the rate, noise simulation"*.
What happened instead is worth reading, because the failure was not in the
verification - it was in what the verification revealed.

```
   PLANNED                          ACTUAL
   ------------------------------   ------------------------------
   verify 100 dates                 43 dated buildings exist, total.
                                    There were never 100 to verify.

   publish the error rate           The dates are not "sometimes wrong".
                                    They are systematically one-sided:
                                    OSHA inspects sites that are ALREADY
                                    OPERATING, so every date is an UPPER
                                    BOUND, not a noisy estimate.

   noise simulation                 A noise model assumes errors are
                                    centred on the truth. These are not.
                                    Measured lags between opening and
                                    first inspection, on the five sites
                                    with an independent opening month:
                                      4, 13, 57, 69, 345 months.
                                    The bound held 5 of 5 times. The
                                    looseness is the problem, not the
                                    validity.
```

> **The engineering lesson, which generalises.** The mitigation assumed the
> defect was **noise** (random, centred, simulable). It was **bias** (one-sided,
> structural, not simulable). Those need different responses: noise is handled
> with a simulation, one-sided bounds are handled with **interval censoring** -
> a different likelihood, not a different sample. `docs/STATUS.md` lists interval
> censoring as NOT STARTED, and it is the specification the data actually calls
> for.
>
> When you write a mitigation, write down which of the two you think you are
> facing. Getting that wrong means your mitigation runs, passes, and mitigates
> nothing.

---

## 7.12 Part 7 self-check

1. Why is this not a distributed-computing problem, and what would you say if
   someone proposed Spark?
2. What does "nothing above L3 knows where the bytes came from" buy you —
   name two things.
3. Explain content-addressed caching and why it matters on day one.
4. Why did routing nearly break the project, and what replaced it?
5. Which data contract catches a *silent* failure, and what does that failure
   look like?
6. Why develop on 200 ZCTAs rather than the full 2,413 pilot set?
7. Why do the builder and the layout linter share measurement code?
8. What is the acceptance test for reproducibility, and who should run it?
9. Walk the L4 box. Which components work, which model is fitted but returns a
   negative result, which model is retired, and which one does not exist at
   all?
10. Run `pytest` now and quote the result with a timestamp. The suite was
    observed at five different states in two hours on 2026-09-14. What does
    that tell you about quoting a count from a document?
11. This section has now corrected its own test count three times. What is the
    structural fix, and why is a prose number a liability? Name two other
    places in the project where the *same* defect appeared.
12. Name the two xfails and the shape they have in common.
13. Which rows of the risk register have already fired? For the facility-dates
    row, why did the planned mitigation not help (hint: noise versus bias)?
    For the `objective.py` row, why is it the most damaging of the set even
    though it is not the largest number?
14. What was the Monte Carlo's draw count, what is the number in `scope.json`,
    and why is the difference the kind of thing an examiner checks first?
15. Why is every Monte Carlo band a *floor* rather than a range?
16. Is the repository under version control, and what is the difference between
    that question and "is the work committed?"

---

**Next:** `VIVA_QA.md` — the questions you will actually be asked, with
answers.
