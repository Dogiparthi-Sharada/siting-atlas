# Interview stories — STAR, and only things that happened

*Written 2026-09-15, figures and artefact paths re-checked 2026-09-16. Six
stories. Every figure is on disk in `outputs/metrics/`,
`experiments/*/artefacts/`, `src/` or `logs/` and the file is named under each
one, so that an interviewer who asks "show me" can be shown.*

**Three of these six are about my own mistakes.** That is deliberate and it is
not modesty. A candidate who can narrate an error, the mechanism behind it and
the fix reads as senior; a candidate with six successes reads as junior, or as
someone whose work was never checked. Do not soften them into near-misses in
the room — the version where nothing actually went wrong is worse than the
version where it did.

**What to do if an interviewer pushes on a number.** Say what the artefact
says, including the caveat, and stop. Several numbers in this project's own
prose are stale against regenerated artefacts; the defence against being caught
out is to have read the JSON that week, not to have memorised a document.

---

## 1. Recovering 1,904 records from a PDF with no table layer

**Situation.** The target variable for the whole project was a facility list
that exists only as a 117-page industry PDF. `pdftotext -layout` returns 1,074
lines for the whole document, of which roughly 120 are prose. The thirteen
tables are images — 152,915 pixel rows in total, one of them a single strip
26,480 pixels tall referenced from 23 separate pages.

**Task.** Get a structured, checkable facility panel out of it, on a
locked-down compute grid with no tesseract installed, no root, and Python
3.6.8.

**Action.** Three pieces. First, table detection: my initial filter kept images
taller than 5,000 pixels, which silently dropped five of the thirteen tables —
about 8% of the content, with no error. Switching the filter to *width*
(tables render 803–828 px wide; page furniture does not) recovered all
thirteen, and I pinned `EXPECTED_TABLES = 13` so the same failure cannot recur
quietly. Second, structure from geometry: columns from pixel-density valleys in
the x-projection of the word boxes, rows anchored on the postal code. Both took
several iterations — the zero-coverage gutter test returned a single column
spanning the table, and the row anchor had to survive five-digit house numbers,
the table border OCRing as `|`, and wrapped ZIP+4 tails migrating into the next
row. Third, portability: I bundled tesseract with its shared libraries, which
failed on the grid with `GLIBC_2.34 not found` because the compute node's glibc
is older than the build host's. `LD_LIBRARY_PATH` does not fix that, because
the dynamic loader is selected before any environment variable is read, so the
bundle ships `ld-linux-x86-64.so.2` and the wrapper invokes it explicitly with
`--library-path`.

**Result.** 1,904 facility records across all thirteen tables, 92.8% carrying a
postal code, 74.6% an opening year. On the table that mattered most, the three
row-anchoring fixes moved it from 510 rows with 41 merged to 535 with 18. 635
of the 1,904 are the facility class the panel admits, and 589 of those merged
in as new rows, taking the panel from 104 facilities to 693 across 230 metro
areas and all 50 states.

**Evidence.** `outputs/metrics/mwpvl_extraction.json`, `mwpvl_merge.json`;
`docs/data/MWPVL_OCR_PIPELINE.md` §3, §7, §8;
`logs/mwpvl_ocr_20260914_060420.log`; `scripts/grid/bundle_tesseract.sh`.

---

## 2. Making the pipeline safe to run twice

**Situation.** The extraction takes about eleven minutes across 62 workers plus
six single-threaded minutes of image extraction, and it gets re-run. Early runs
produced results nobody could tell apart afterwards.

**Task.** Make it so that a second run either reproduces the first or refuses.

**Action.** One entry point, `scripts/grid/run_ocr.sh`, no arguments, runnable
from any directory. Distinct exit codes so a failure is diagnosable from the
return value alone — 2 for a missing PDF, 3 for the venv, 4 for a missing C
binary that pip cannot supply, 5 for OCR failure, 6 for "it ran and produced
nothing". A preflight that runs `tesseract --version` with a 30-second timeout
*before* spending six minutes extracting images, with three distinct diagnoses
attached to the three ways it can fail. A `SETTINGS.json` stamp written into
the output directory on first use, which refuses to resume if the upscale, psm,
strip or overlap differ — because resume works by filename, so a changed
parameter would silently blend two extractions and the row counts would look
fine. Image reuse only when the workdir holds exactly the image set the PDF's
own listing calls for, strict in both directions. And the bundle builds into a
staging directory and is moved into place with `rename(2)`, because the first
version did `rm -rf` in place and took down a running job: 62 workers were
exec'ing out of that directory, their next exec hit ENOENT, and the process
pool propagated the first `FileNotFoundError` and aborted everything.

**Result.** The specific failure that forced most of this is preserved in the
logs. A run that attempted 120 strips, failed all 120 and wrote nothing printed
`SUCCESS in 14m 6s -- 36 TSV files`, because 36 files from an earlier run were
sitting on disk. The banner now counts files *this run* produced:
`SUCCESS in 11m 26s -- 120 new, 156 total TSV files`.

**Evidence.** `scripts/grid/run_ocr.sh` lines 19-25 and 142-151;
`grid_ocr.py` lines 126-156, 189-221, 251-282;
`logs/mwpvl_ocr_20260914_060757.log` versus `..._062734.log`.

---

## 3. The optimiser that returned a wrong answer and said nothing

**Situation.** A conditional-logit estimator I wrote, used by every experiment
in the project. Two bugs in it, found a day apart, both silent.

**Task.** Work out why one covariate experiment printed `nan` in a mean, and
separately why a family of five new covariates all "worked" when none of them
should have.

**Action.** The first was three lines from the answer once I looked. The
multi-start loop keeps the best result with `if r.fun < best.fun`. Every
comparison against NaN is False, so a NaN from the *first* start can never be
displaced by any later start, however good — `fit` returns an all-NaN
coefficient vector with no error and no warning, and it propagates into every
downstream metric. The cause is an unlucky BFGS excursion overflowing the
parameter, making the utility `inf`, and `inf/inf` NaN. I added a finiteness
guard, and a hard `RuntimeError` when every start comes back non-finite.

The second was subtler and I found it by distrusting a pattern rather than a
number. Five log-relative covariates all produced a coefficient, and I noticed
that in all five, the direction that "found" an effect was the direction with
the *lower* feasibility ceiling. That is, success was predicted by how cheap it
was to violate positivity. The estimator parameterises utility as a linear
index that must stay positive; nothing was checking the *non-chosen*
alternatives. The optimiser had discovered it could shrink the denominator by
pushing them below zero.

**Result.** Measured: the optimiser had driven coefficients 20x to 77x past the
feasibility ceiling, putting between 765 and 4,816 non-chosen alternatives at
negative probability, inflating the chosen probability from 0.078685 to
0.079346 and the log-likelihood by up to 1.204. The log-likelihood is perfectly
finite the whole time, which is why the first bug's guard cannot catch the
second one. The check now raises. It fired for real on a later run, which is
published at 41 re-splits instead of the 50 it was launched at — I reported the
short run rather than dropping the failing arm.

**What I would still fix.** The identical unguarded comparison is still in
`choice_bootstrap.py:110`, on the inference path, reached by every bootstrap
replicate, and nothing tests it. I know about it and it is not done.

**Evidence.** `src/siting_atlas/models/choice.py` lines 272-295 and 299-334;
`experiments/percapita-logrel/artefacts/logrel_search.json` (`diagnose.columns[*].beta_over_beta_max`);
`docs/research/NOTES_LOG_RELATIVE.md` §3.1 and lines 262-278, 335-358.

---

## 4. Finding fabricated values in my own figures

**Situation.** A self-audit of all fourteen generated figures, run because an
earlier sweep had already caught two figures printing pre-registered *targets*
as if they were measurements.

**Task.** Establish, for each figure, whether its numbers come from an artefact
or from a literal array in the plotting code.

**Action.** Read every figure's source. The standing tally is that 12 of the 14
contain no real results; most of those are labelled as schematics and are fine.
Two were not. One plotted a distance-decay curve with a shaded band legended
"95% CI" and an annotation reading "-0.4% n.s." — an interval and a
significance test, on nine typed numbers, for a regression that has never been
run, against a y-axis (two-day order volume) that is a quantity this project
does not observe at all. Its absence is the documented reason that estimand was
abandoned. The other hard-coded eight tornado swings with per-bar dollar labels
and no disclosure anywhere, while the caption asserted the decomposition as
measured fact; the underlying artefact has aggregate bands only and no
per-bucket breakdown.

The precedent I was working from was worse and had already been fixed: a
backtest figure printing AUC 0.84, PR-AUC 0.31 and precision@100 of 0.61, whose
ROC "curve" was `tpr = fpr ** (1/0.84 - 1)` — an analytic curve chosen so its
area would equal the number printed beside it. And a rank-stability figure that
invented eight specific ZIP codes holding positions across 10,000 Monte Carlo
draws that were never run.

**Result.** Both were fixed the same day. The band and the significance
annotation are gone; the curve is a single dashed unlabelled line; and the
disclaimer is drawn *inside the axes* rather than in the caption, because the
caption stays in the document and the figure ends up in a slide. The measured
replacements for the fabricated backtest numbers are AUC 0.6894 against 0.5000,
Brier 0.019522 against a constant's 0.019614, and calibration error 0.00863
against 0.00005 — the model is 173x worse calibrated than a constant.

**The honest framing.** These were not written in bad faith; they were
pre-registered targets and illustrative shapes that were never removed when the
real numbers arrived. The failure mode is lag, not lying, and the defence is
mechanical: derive the number rather than type it, and put the caveat where
cropping cannot reach it.

**Evidence.** `docs/data/FIGURES.md` lines 97-118;
`tools/figures/fig_methods.py` lines 73-91, 215-233;
`docs/figures/README.md` lines 9, 186-232;
`experiments/hazard-model/artefacts/hazard_report.json`.

---

## 5. Taking down a shared machine after being told not to

**Situation.** A shared six-core workstation in interactive use by other
people. The brief on this project was explicit: single-threaded,
`os.nice(19)`, and if 50 re-splits proved too slow, cut the repeat count rather
than parallelise. That instruction is written into two of my own module
docstrings, which record the box sitting at load average 24 and 25 when those
experiments were written.

**Task.** Run a four-stage covariate experiment inside a working day.

**Action.** I used a five-process pool anyway. Parallelism buys wall clock and
nothing else here, because the repeats are independent by construction — so the
only thing it bought was other people's cores.

**Result.** Load average 44 on six cores. The run had to be killed, and it
wrote its artefact once, at the end, after four stages — so forty-five minutes
of completed, correct, finished work was discarded because it existed only in
memory. Two other experiments on the project were collateral: one reached 45 of
50 re-splits and was starved to under 2% of a core, and its artefact does not
exist; another got 1.1% of one core against 96.5% for a sibling process at
identical nice, and four of its eleven arms never completed and are absent from
the results rather than being summarised over fewer repeats.

**What changed.** Six things, and they are the part of this story worth
telling. Every entry point now sets `os.nice(19)`, single process,
`OMP_NUM_THREADS=1`. Every experiment persists after each stage, so a finished
stage is on disk before the next one starts. Artefacts carry a stage ledger
marking each stage as ran / carried-forward / absent, so an artefact cannot
claim to have been regenerated when it was not. Experiments are arm-major with
a pre-declared priority order, checkpointed after every fit, so an interruption
leaves a prefix of complete arms rather than every arm equally unfinished — and
the order is declared in advance, because an order chosen after seeing the
results is a selection rule. The repeat count is written into the artefact
rather than left to a default nobody checked. And unfinished work is reported
as unfinished, because a missing section with no explanation is how a null
result gets quietly improved.

**The gap I will admit to.** One of those ledgers is built *before* the stages
run, so an interrupted run can still write an artefact asserting that a stage
which never executed "ran this invocation" — the exact claim the ledger exists
to prevent.

**Evidence.** `src/siting_atlas/models/covariate_harness.py` lines 20-29;
`docs/research/NOTES_COVARIATE_SEARCH.md` lines 635-647, 798-818;
`docs/research/NOTES_PERCAPITA.md` lines 378-384, 430-433;
`docs/research/NOTES_GRAVITY_NETWORK.md` lines 617-626;
`src/siting_atlas/models/covariate_search.py` lines 173-177 for the gap.

---

## 6. Auditing my own key variable for circularity, and withdrawing my own claim

**Situation.** One covariate — the count of warehousing establishments in an
area — carries the entire model. The other three parameters sit at 1e-16, and
an ablation says removing it costs 7.7 of 38 held-out hits, winning 50 of 50
paired re-splits. It is also the covariate most likely to be circular: a
warehouse count measured *after* the opening includes the building whose
opening is being predicted.

**Task.** Separate contamination from genuine agglomeration. An ablation cannot
do it — both hypotheses imply the covariate predicts.

**Action.** I built an honest-vintage arm. For the 29 decisions where I could
establish a true pre-opening date, I re-read the covariate from a data vintage
that predates the opening, and compared three arms: the potentially
contaminated one, the honest one, and no covariate at all.

**Result.** 8.22 held-out hits of 12 for the honest arm against 9.24 for the
contaminated one and 4.48 with no covariate. So 78.6% of the covariate's value
survives the removal of any possible leak, and the per-establishment
coefficient moves by 1.2%. The variable survives.

**The caveats I attach, unprompted.** The honest arm reads an *older* vintage as
well as a cleaner one, so removing the leak and adding staleness are the same
intervention — the gap is an upper bound on the leak, not a measurement of it.
n is 29, and those 29 are not a random subsample; they are what the source lists
and the address matcher reaches, and that is an easier set than the full panel.
And on the cleanest subset of fifteen, the contaminated arm's advantage falls to
0.34 hits with 24 wins, 15 ties and 11 losses, which is close to a coin flip.

**The related story, if they want a second one.** On a different arm I
published a coefficient interval that excluded the baseline — the first in the
project's history. It came from the 2.5–97.5 percentile of 50 re-split fits,
which is not a standard error and is not even an interval on the same estimator
as the point estimate beside it. I ran three proper ones: a bootstrap clustered
over 194 metros, a metro-clustered sandwich and an independent sandwich. All
three contain the null; the clustered p-value is 0.065. I withdrew the claim
the same day, left the superseded numbers in place with a banner rather than
deleting them, and the general rule I took from it is in the artefact: a
percentile over re-splits is not an interval and should not be quoted as one.

**Evidence.** `outputs/metrics/leakage_decisive.json`, `leakage_test.json` and
`choice_report.json` (`inference`);
`experiments/gravity-network/artefacts/network_inference.json`;
`docs/research/COVARIATES_TRIED.md` §5.1;
`docs/research/NOTES_PANEL_EXPERIMENTS.md` §12.

---

## Two shorter ones, for when they ask for a third example

**"Tell me about something you built that worked."** A parcel-level
cost-to-serve model over 2,333 ZIP-code areas using a Daganzo-style continuous
approximation of tour length, run across five stress scenarios. Median
$1.082994 per parcel, p10 $0.98, p90 $1.42. The interesting part is the
sensitivity: I deleted the routing term the module is named after and the
median moved 3.9%, with 88 of the cheapest 100 areas still in the cheapest 100.
The headline is carried by service time, parcels per stop, the van lease and
the labour-hours denominator — and three of those four have no published
source. The routing mathematics is decoration, and I would rather say that than
let someone find it.
*Caveat to carry:* the "334 depots across **11** CBSAs" phrasing that appears
in the project's prose is wrong in the CBSA count only. The priced table covers
**ten** metros, and 334 is the sum over those ten of
`ceil(metro daily parcels / 40,000)` — recomputed straight from the baseline
parquet, and what the solver actually opens. `cost/params.py:220`'s "~329" is a
different and equally correct quantity: one national division, 13,152,992 /
40,000 = 328.8. Say "334 across the ten priced metros" or "329 nationally", and
never either one without saying which.
`outputs/metrics/cost_report.json`; `docs/research/NOTES_daganzo_1984.md`.

**"Give me a debugging story that isn't a bug in your own code."** A published
headline in the project had drifted across drafts — 330 activations, then 317,
then 282 — and the open question was whether a parameter change was doing it. I
ran a 500-draw parameter sweep over the optimiser to find out. It was not: 282
sits at the 67th percentile of the band and 330 at the 97th, so the mover was
depot placement, which the sweep does not treat as a parameter at all. Two
things travel with that answer: one input was left unsampled by oversight, so
every band is a floor; and the capital figure is exactly $4m × n in all 500
draws, so $1.128bn, $1.268bn and $1.320bn are three activation counts restated
in dollars, not three financial findings.
`experiments/portfolio-optimiser/artefacts/montecarlo_report.json` and
`portfolio_report.json` in the same directory.
