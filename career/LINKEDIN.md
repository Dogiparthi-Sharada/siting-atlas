# LinkedIn — drafts that are postable as written

*Written 2026-09-15. Every number below was read off an artefact in
`outputs/metrics/` or a file in `src/` on that date. The source is named in
the checking notes under each post, which are **not** part of the post — strip
them before posting.*

Four posts, a headline and an About paragraph. They are ordered by how safe
they are: post 1 is an unambiguous achievement and can go out today; post 4 is
the shortest and the easiest to get wrong.

**The rule that governs this file** is the one `PORTFOLIO_PLAYBOOK.md` §4
already states: never post a number you have not read off an artefact that
morning. Several figures in the repo's own prose are stale against regenerated
artefacts (see the checking notes), so re-derive rather than re-quote.

Two things to avoid, because they are what makes technical people close the
tab: the one-sentence-per-line cadence, and a closing question that exists to
farm comments. None of the drafts below has either. Do not add them.

---

## Post 1 — the extraction

An industry PDF I needed had 1,904 facility records in it and no table layer.
`pdftotext -layout` returns 1,074 lines for 117 pages and about 120 of them are
prose; the tables are pictures — thirteen of them, 152,915 pixel rows in total.

OCR gives you words and bounding boxes, not a table, so the structure has to be
recovered from geometry. Columns came from pixel-density valleys: project every
word box onto the x axis, count how many words cover each pixel column, and cut
in the middle of each sustained low-density run. My first version looked for
gutters containing *zero* words and returned one column spanning the entire
table, because over 540 rows some description always overflows. The gutters are
shallow, not empty — 1,385 words down the centre of the address column against
three in the gutter beside it, and the narrowest real gutter measured 13 pixels.

Rows came from anchoring on the postal code, which is the only token in an
address column shaped like one. That needed three more fixes. A row occupies
the space *above* its anchor rather than below it, and row gaps of 48 and 64
pixels occur in the same table, so fixed banding does not work. A five-digit
house number matches the same regex as a ZIP, and treating it as an anchor
invents a facility that does not exist. And the table's vertical border OCRs as
a `|`, which makes a legitimate anchor look like it has something after it, so
the anchor is rejected and two buildings merge into one. Before the three
fixes: 510 rows, 41 of them merged. After: 535 rows, 18 merged.

The grid this ran on has no tesseract, no root, and Python 3.6.8. I built a
relocatable bundle, which failed on the first grid run with `GLIBC_2.34 not
found` — the compute node's glibc is *older* than the build host's, and
`LD_LIBRARY_PATH` does not help, because the dynamic loader is chosen before
any environment variable is read. The fix is to ship `ld-linux-x86-64.so.2`
inside the bundle and invoke it explicitly with `--library-path`, so the host
runtime is never consulted at all.

The bug I liked least was silent. `tesseract in out --psm 6 tsv` — `tsv` is not
a flag, it is a config file that has to exist inside the bundle. Without it
tesseract prints one warning, writes plain text instead of TSV, and exits zero.
Sixty-two workers each did six seconds of real OCR and discarded it, and the
run looked healthy the whole time.

> **Checking notes (strip before posting).** 1,904 / 13 tables / 58,088 words:
> `outputs/metrics/mwpvl_extraction.json`. 152,915 pixel rows, 117 pages, the
> `pdftotext` line count, the 1,385-vs-3 gutter measurement, the 13-pixel
> minimum, the 48/64-pixel row gaps and the 510/41 → 535/18 before-and-after:
> `docs/data/MWPVL_OCR_PIPELINE.md` §2, §3, §7, §8. The 517-of-535 merge figure
> is stated in that doc as a working measurement **not** reproducible from an
> artefact — quote the 41 → 18 framing, which is in the same section, and not a
> percentage. GLIBC failure verbatim: `logs/mwpvl_ocr_20260914_060420.log`.
> Loader fix and the `tsv` config trap: `scripts/grid/bundle_tesseract.sh`
> lines 15-32 and 128-151. Python 3.6.8 and the Pillow 8.4.0 pin:
> `MWPVL_OCR_PIPELINE.md` §11 — note that §11 is stale on the bundle itself,
> claiming glibc was deliberately left behind; the shipped script does the
> opposite and the log is the evidence.

---

## Post 2 — the pre-registration that failed

On 15 September I wrote down what would count as the model working, hashed the
file, and then fitted the model. The hash is in the results artefact:
`946f7ef75db69e5278eea409a04c3823`. The pre-registration was written at 22:49
UTC; the model wrote its output at 23:13.

The criterion had two clauses. The metro-level model had to beat a "rank by
number of households" baseline on AUC in a majority of held-out years, **and**
its calibration had to be at least as good as a constant in a majority of
years. The second clause was there deliberately, because an earlier
specification on the same project had scored AUC 0.689 while losing every one
of its 17 calibration comparisons to a constant, and a ranking you cannot
calibrate cannot tell a county whether "more likely than your neighbour" means
5% or 40%.

The result was 0 of 7 years on AUC and 3 of 7 on calibration. It was not close:
the model runs 0.61 to 0.81 across the held-out years and the households
baseline runs 0.84 to 0.97. I then ran it eighteen ways — three
covariate-admissibility arms, three functional forms, two window definitions —
and the answer is the same in all eighteen.

Two things I would do differently. The pre-registration contained a rule that
any covariate whose data vintage post-dates the year being predicted gets
dropped and the drop gets counted. That rule is right, and applied honestly it
dropped 10 of my 12 covariates, so the test of the hypothesis ran on two. I
should have checked admissibility before committing to a hypothesis that needed
twelve. Separately, the households baseline is scored using the same Census
column the vintage rule forbids the model to use — which biases the comparison
against my own hypothesis. That is written into the artefact, because it is the
direction that makes a null result safe to report rather than the direction
that would have made it convenient.

> **Checking notes (strip before posting).** Prereg text, criterion wording,
> declared verdict arm: `docs/PREREG_METRO_MODEL.md` §5, §7, §9. Hash,
> timestamps, per-year AUC table, 0/7 and 3/7, the 18 arm × form × scope
> combinations, the four self-logged deviations including the baseline-bias
> note: `outputs/metrics/metro_entry.json` (`prereg_md5`, `criterion`,
> `written_at 2026-09-15T23:13:41+00:00`, run `20260915-231322-7d21`). The
> AUC 0.689 / 17-of-17 calibration loss is the retired hazard model:
> `experiments/hazard-model/artefacts/hazard_report.json` and
> `hazard_revival.json` in the same directory
> (`calibration_against_constant`; `verdict.retirement_stands: true`).
> **Do not** write "a model with AUC 0.689 is
> useless" — say what the artefact says, that it lost every calibration
> comparison.

---

## Post 3 — a screening test worth one groupby

Before fitting any conditional model — conditional logit, a within-group
ranker, anything that learns from differences inside a group rather than across
the whole sample — compute each candidate covariate's coefficient of variation
*within* the groups you are conditioning on. Not across the sample. Within.

On 21 terms measured across 41 metros and 8,271 candidate ZIP-code areas, the
result is one-directional rather than symmetric, and the asymmetry is the
useful part. Seven terms had a within-metro cv below 0.6, and **all seven**
landed on the boundary: the fitted coefficient pinned at zero, the variable
contributing nothing. Fourteen had a cv above 1.3, and **nine** of those
fourteen came back interior — so low dispersion is enough to predict failure,
while high dispersion only buys a chance of success. Nothing in the sample fell
between 0.59 and 1.40. The five high-dispersion terms that still failed all
measure the same side of the network, which is a second thing worth knowing:
the screen tells you what to drop, not what to keep.

What makes me think it is the dispersion and not the variable is that I could
turn it with a dial. Eighteen of the 21 terms are gravity measures of the form
"sum over facilities of mass divided by distance to the power alpha" — the same
facilities, the same masses, with only the exponent changing how sharply the
measure discriminates between two areas inside one metro. At alpha = 1 the cv
runs 0.30 to 0.44 and all six terms sit on the boundary. At alpha = 2 the cv
runs 4.4 to 5.5 and four of six are interior. At alpha = 3 the cv runs 6.8 to
8.5 and again four of six are. Same information, sharpened; the coefficients
that move go from none to two thirds of them.

The honest limit is that this is 21 columns of one family on one panel, one
run, so it is a correlation with a plausible mechanism rather than a
demonstration — and the terms are not independent of each other. The five
high-dispersion failures are the counter-examples, and they are why I will not
claim the second direction: dispersion buys the coefficient room to move, it
does not put anything worth finding in that room. Use it as a screen anyway,
because it costs one groupby and, in the direction that holds, it fails loudly.

The intuition is just conditional logit's identification restated. The model
learns only from differences between the alternatives inside a choice set. A
covariate that is nearly constant within the group has nothing for it to learn
from, however much it varies nationally — which is exactly the case where a
correlation matrix computed on the pooled sample will tell you the variable
looks promising.

> **Checking notes (strip before posting).** All cv values, the 41-metro /
> 8,271-candidate frame and the alpha-1/2/3 blocks:
> `experiments/gravity-network/artefacts/gravity_network.json`
> (`terms.dispersion`, run `20260915-210603-b780`). The interior/boundary call
> for each term comes from `arms.<arm>.verdicts.<col>.state` in the same file,
> which covers all 21 terms — **not** from `boundary_census`, which covers only
> 5 of them and is too thin to carry the claim.
> **Do not write "21 of 21 each way," and do not write "7 of 7 and 14 of 14"
> either.** `docs/PREREG_METRO_MODEL.md` lines 40-44 and `MODELS_EXPLAINED.md`
> §7 use the first phrasing, which reads as 42 observations; an earlier
> correction pass in this folder replaced it with the second, which is also
> wrong. The counts are **7 of 7 below cv 0.6 at the boundary** and **9 of 14
> above cv 1.3 interior** — the rule is one-directional. (Strictly the second
> count is 8: `fulfilment_proximity` is interior in two arms and
> boundary-straddling in a third. Nine counts a term as interior if it is
> interior in any arm. Do not put that nuance in a post; do have it ready if
> someone opens the artefact with you.) **Do not call it causal** —
> `docs/research/NOTES_GRAVITY_NETWORK.md` §5 says in terms that it "is not a
> causal demonstration", and `MODELS_EXPLAINED.md` §7 upgrades it past what its
> own source allows. The draft above uses the source's framing, not the
> summary's.

---

## Post 4 — what I would do differently

Four things, in the order they cost me the most.

I did not check the unit of analysis before writing the model. The panel
recorded 812 openings as area-quarter events; they were 94 real decisions, each
switching on a 15-mile circle of ZIP-code areas — a median of 39 areas per
opening. The model spent its capacity learning to draw circles. This is one
paragraph of a discrete-choice textbook and I read it after the model failed
rather than before it was written.

I did not check covariate dispersion before choosing a specification. Several
of the terms I fitted were nearly constant within the group I was conditioning
on, which pins the coefficient at zero regardless of how informative the
variable is. One groupby, up front, would have told me.

I wrote experiments that persisted their results at the end rather than after
each stage. On a shared six-core box at load average 44 one of them had to be
killed, and forty-five minutes of completed, correct work went with it, because
it only existed in memory. Everything since checkpoints each stage to disk as
it finishes, and records in the artefact which stages actually ran in that
invocation.

I put a confidence band on a chart before there was a model behind it. The
numbers were typed into an array, the legend said "95% CI", and an annotation
said "n.s." — a significance test on a quantity the dataset does not contain.
It was disclosed as illustrative in the caption of the document it appeared in,
and figures get lifted out of documents. The caveat now sits inside the axes,
where cropping into a slide cannot remove it.

> **Checking notes (strip before posting).** 812 → 94:
> `experiments/hazard-model/artefacts/hazard_report.json`. The median-39
> catchment: `hazard_revival.json` in the same directory,
> `provenance.catchment_load.zctas_per_opening.median` (mean 52.4, p90 105,
> max 317, at the 15-mile radius). Do not confuse it with the **13** in
> `zctas_first_switched_on`, which is the median number of areas an opening
> switches on *for the first time*; only the 39 supports the
> independence argument.
> Load average 44 and the 45 minutes: `src/siting_atlas/models/
> covariate_harness.py` lines 20-26 and `docs/research/NOTES_COVARIATE_SEARCH.md`
> lines 807-812. The typed interval and the `n.s.` annotation:
> `docs/data/FIGURES.md` §fig05 and `tools/figures/fig_methods.py` lines 73-91.

---

## Headline

Primary — 138 characters:

> MSBA candidate · data engineering and applied research · I recover data from
> sources that resist it, then test the result hard enough to lose

Two alternates, if the primary reads as too clever for the roles being targeted:

> MSBA candidate · Data Engineering / Analytics Engineering · OCR and pipeline
> recovery, DuckDB, reproducible builds, pre-registered evaluation

> MSBA candidate · Applied research and public-interest analytics ·
> Discrete-choice models, pre-registration, and negative results I published

Do not use "aspiring". Do not use "passionate about data".

---

## About section

> I work on the part of an analytics project that decides whether the rest of it
> means anything: where the data came from, whether the build reproduces, and
> whether the result survives a test that could have gone the other way.
>
> On my MSBA capstone — an open model of where parcel-delivery infrastructure
> gets built, from public data only — the data engineering is the part I would
> point at first. I recovered 1,904 facility records from a 117-page industry
> PDF with no extractable table layer, by rebuilding the table geometry from
> OCR word boxes: columns from pixel-density valleys, rows anchored on postal
> codes. I validated the output three independent ways, the sharpest of which
> checks each claimed opening date against OSHA inspection records that prove
> the building was already operating — 197 of 208 checkable records pass. Then
> I hardened it for a locked-down compute grid running Python 3.6: one entry
> point, distinct exit codes per failure mode, a settings stamp that refuses to
> resume a run under different OCR parameters, and a success banner that counts
> only files the current run produced, after an earlier version reported
> success on 36 files left over from a previous one while writing none.
>
> The modelling largely did not work, and I can tell you precisely how I know.
> I pre-registered the success criterion with a timestamp and an md5 before
> fitting; the model failed it in 0 of 7 held-out years, and the failure holds
> across all 18 specifications I tried. Along the way I audited my own key
> covariate for circularity against a pre-opening data vintage, found and fixed
> three bugs in my own estimator — including one where the optimiser was
> gaining likelihood by pushing alternatives below zero probability, which has
> a perfectly finite log-likelihood and therefore triggers nothing — and
> withdrew a significance claim I had published myself, after four proper
> estimators all contained the null.
>
> One transferable result came out of it. Measure a covariate's within-group
> coefficient of variation before you fit a conditional model: below about 0.6
> it will contribute nothing — that held for all seven such terms I measured.
> Above about 1.3 it has a chance and no more; nine of fourteen worked. It
> costs one groupby, it is a screen for what to drop rather than a promise
> about what to keep, and it would have saved me a month.

> **Checking note.** 197 of 208 and the 94.7% pass rate are the *current*
> `outputs/metrics/mwpvl_validation.json`; several docs in the repo still quote
> the earlier 157 / 10 / 93.6% run. Read the artefact on the day you publish.
