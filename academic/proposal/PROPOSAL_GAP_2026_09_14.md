# PROPOSAL_V5 gap report — 2026-09-14

*Every claim in `docs/proposal/PROPOSAL_V5.md` that the artefacts no longer
support, with the artefact that settles it. Written against
`PROPOSAL_V5.md` as of 2026-09-14 14:13 and the contents of
`outputs/metrics/` as of 2026-09-14 15:00. Line numbers are from that
revision of the Markdown and will move once the fixes land.*

Companion: `docs/AUDIT_2026_09_14.md` §6.1 (which opened this item),
`../PROGRESS_2026_09_14.md` (the approved framing), and `README.md` in this
folder (the build and staleness index).

---

## 0. How to read this

The document's own closing rule is *"If any figure here disagrees with the
artefact, the artefact is right and this document is out of date."* This
report applies that rule mechanically. Three classes:

```
  WRONG        the statement asserts something the artefacts contradict.
               Fixed in phase 1, regardless of what any other work produces.
  MISSING      the statement is true as far as it goes and omits work that
               changes what a reader concludes.  Phase 2.
  PENDING      the correct replacement text depends on ranked item 5
               (wiring the expanded panel into the warehouse) or item 6
               (geocoding the 700 addresses), both in flight.
```

The single largest defect is not any one line. It is that **the document has
zero mentions of the 700-row panel, of the 1,904-facility extraction, or of
the 1,420 recovered opening dates**, and therefore describes a project whose
binding constraint is still in place. Verified:

```
$ for t in MWPVL expanded 700 1,904 OCR; do \
    echo -n "$t: "; grep -c "$t" docs/proposal/PROPOSAL_V5.md; done
MWPVL: 1     expanded: 0     700: 0     1,904: 0     OCR: 0
```

---

## 1. WRONG — fixed in phase 1

### G1. "We decline to buy the same panel" — §2.2, line 373

> *"Houde, Newberry and Seim obtained the network from the supply-chain
> consultancy MWPVL. **We decline to buy the same panel**, and §4.3 gives the
> reason."*

Not merely stale. **Actively misleading**, and in the direction that costs
the project the most. A reader concludes the project chose not to obtain this
data. What actually happened is the opposite and is a better story: the
project bought nothing and extracted a **free public article** — a different
document from the commercial panel, at a different vintage, by OCR.

- **Settled by:** `docs/data/MWPVL_2025.md:3-5` (*"Saved 2026-09-14 from
  `https://mwpvl.com/html/amazon_com.html`, 117 pages, 11.3 MB … **Not
  purchased** — the public page, printed to PDF"*);
  `outputs/metrics/mwpvl_merge.json` `by_source_dataset.mwpvl_2025q1` = 596
  of the 700 panel rows.
- **Also:** the sentence sits in Related Work as a *methodological* position.
  The position it should state — free public article yes, commercial panel
  no — is the project's whole thesis and is currently made nowhere.

### G2. "The free table is a snapshot of 2012" — §4.3, line 991

The failed-routes block lists:

```
  a commercial industry census     the free table is a snapshot of 2012
```

That is true of `data/raw/mwpvl/Amazon.com Distribution Network Strategy.pdf`
and **false of the document actually used**. `MWPVL_2025.md:44-50` records
the distinction explicitly: the 2012 file is a different document; the 2025
Q1 article carries a dedicated delivery-station section spanning twenty-eight
pages. The row belongs in the WORKED block, not the failed one.

- **Settled by:** `docs/data/MWPVL_2025.md` §1; `outputs/metrics/
  mwpvl_extraction.json`.

### G3. The WORKED block stops at OSHA — §4.3, lines 999-1003

```
  WORKED: US DOL OSHA bulk extract
    5,200,011 inspections -> 951 Amazon rows -> 474 buildings
    -> 93 in the pilot metros -> 43 dated delivery stations
```

A second route worked, on 2026-09-14, and produced the thing the first route
structurally cannot produce: an **opening date** rather than an upper bound.

- **Settled by:** `outputs/metrics/mwpvl_extraction.json` — 13 table images,
  1,904 facilities, 1,420 with a year, 873 with a month, 635 US small-package
  delivery stations (sums verified across the `tables` array).
- **And:** `outputs/metrics/mwpvl_validation.json` — 93.6% against the OSHA
  operating-by bound (157 linked, 10 falsified).

### G4. "We have decided not to buy it" — §4.3, lines 1094-1103

The decision paragraph is still correct in its *conclusion* (the commercial
XLSX was not bought) and wrong in everything a reader takes from it. It
describes the MWPVL panel as *"item for item, the panel we spent a day
failing to build"* — a day that has since succeeded, from the free channel.
It also omits the finding that is the strongest single piece of evidence in
the project:

> *"in future we will no longer be updating this information online due to
> the high rates of plagiarism of this content … If there is an interest in
> obtaining current information available in XLSX format then please contact
> us and we can provide details regarding the commercial terms."*

- **Settled by:** `docs/data/MWPVL_2025.md` §2, quoting lines 47-51 of the
  source verbatim.
- **Why it matters here rather than in a footnote:** the project's claim is
  that the asymmetry between an operator and a county planning department is
  **price, not scarcity**. This is that claim stated by the seller.

### G5. "the benchmark … was never fitted" — §3.2, lines 719-726

> *"The benchmark was pre-registered as an **atheoretical gradient-boosted
> ranker** and that model was never fitted."*

It has been fitted, on identical splits, over 50 paired re-samples.

- **Settled by:** `outputs/metrics/gbm_benchmark.json`, `across_repeats`,
  `n_repeats` 50, seed 20260914, 94 decisions, 38 held out:

```
  top-10 of 38, mean over 50 re-splits    mean     sd     Brier
  ------------------------------------------------------------------
  conditional logit                      20.60   2.72   0.007550  <- best
  warehouse count, unfitted              20.96   2.50   0.007793
  gbm stump/200 levels                   22.30   2.61   0.007685
```

- The paragraph's *prediction* was right ("a boosted ranker would probably
  have out-ranked the structural model") and should be scored as such rather
  than left in the future tense. The margin is **1.70 hits of 38**, against
  per-method re-sample sd of **2.44 to 2.92** — i.e. the spread across all
  eight methods is smaller than any one method's own noise.

### G6. "MET, AND IT WINS" — §3.2, line 705

The success-criteria table still scores the benchmark criterion as

```
  benchmark    reported even if it wins    MET, AND IT WINS
                                           (warehousing count alone,
                                            zero parameters)
```

This is the last surviving instance of the "beats" error that §1 (lines
65-75), §5.4 (1763-1786) and `README.md` (183-195) have all already
corrected. Over 50 re-splits the raw count's margin is **+0.36 hits of 38,
paired sd 1.14**, losing 11 of 50 and tying 16.

- **Settled by:** `gbm_benchmark.json`, `across_repeats.conditional_logit`:
  `vs_raw_count_mean` −0.36, `vs_raw_count_sd` 1.1386, `vs_raw_count_wins`
  11, `vs_raw_count_losses` 23.
- **Note the direction:** the criterion was *"reported even if it wins"*, and
  it did not win. "DRAWS" is the honest scoring.

### G7. "on the only evidence available" — §5.4 line 1815, §6-M line 2289

Both passages rest the entire endogeneity-guard argument on **five
addresses** with lags of 4, 13, 57, 69 and 345 months, and say *"on the only
evidence available"*. That is no longer the only evidence available, and the
new evidence is eight times larger and points the same way.

- **Settled by:** `docs/research/NOTES_COVARIATE_LEAKAGE.md:59-69` —
  **n = 42** facilities with a stated opening date that also link to an OSHA
  inspection; gap > 0 months on 41 of 42 (98%), **> 12 months on 37 of 42
  (88%)**, > 24 months on 26 of 42 (62%). Median gap 34 months.
- The claim "the guard is defeated more often than it holds" survives and is
  now measured rather than inferred from five points. Strengthening it is a
  correction, not a softening.

### G8. Timeline week 3 — "NOT YET BUILT" — §9

```
   3  Gradient-boosted ranker as a benchmark, same splits,
      reported whichever way it falls.  Pre-registered in
      Sec. 3.2 and NOT YET BUILT; …
```

Built. Same settlement as G5.

### G9. §3.3 — the coverage artefacts "do not exist"

The artefacts exist and have since 2026-09-13.

- **Settled by:** `outputs/metrics/nlrb_coverage.json` — national two-list:
  n_nlrb 208, n_osha 340, overlap 112, observed union 436; Chapman 629.7
  [575.4, 705.1]; Chao lower bound 899.1 [778.5, 1062.1]; OSHA coverage
  **upper bound 54.0% (Chapman) / 37.8% (Chao)**. A three-list log-linear
  model over NLRB/OSHA/OSM is in the same file.
- Minor: §3.3 says *"209 distinct city-and-state pairs"*; the artefact says
  208 (`national_two_list.n_nlrb`). The artefact wins by the document's own
  rule.
- **Also now available and not mentioned:** MWPVL is a legitimate **fourth
  list** with a genuinely independent capture mechanism. `MWPVL_2025.md` §1
  establishes that the structural-zero exclusion in `NLRB.md` applies to the
  2012 file and must not be carried to the 2025 one.

---

## 2. MISSING — phase 2, and mostly not contingent on anything

### G10. The document's central constraint has been removed and it does not say so

Every account of dating in the document — §4.3, §4.7, §5.4, §6 defects E, M
and O — is written from inside the constraint *"we have upper bounds and no
opening dates."* That constraint was removed on 2026-09-14.

```
  1,904  facilities extracted from 13 table images (152,915 pixel-rows)
  1,420  carry an opening year          mwpvl_extraction.json
    873  carry an opening month
    635  US small-package delivery stations, the target class
```

Validated three independent ways, all artefact-backed:

```
  vs the OSHA operating-by bound   93.6%   157 linked, 10 falsified
                                           mwpvl_validation.json
  date plausibility                99.5%   1,413 of 1,420
                                           (5 OCR-damaged years + 2
                                            delivery-station rows of 790
                                            predating the 2013 launch)
  vs an independent geocoding      99.8%   556 of 557 states agree with the
                                           state implied by the postal code
                                           mwpvl_merge.json.ocr_state_grade
```

For scale, and this comparison belongs in the document because the document
already carries the other half of it: **the satellite method failed the first
of these tests on 36% of its output. This fails on 6.4%.**

### G11. §6 defect O says satellite failure "keeps defects E and M open"

> *"Because the timing factor of §5.4's decomposition needs a lower bound on
> opening dates, and satellite imagery was the route to one, this failure
> also keeps defects E and M open."*

Satellite was *a* route, not *the* route. Another route worked. Defect M is
now **part-closed**: the leak has been sized rather than merely named.

- **Settled by:** `outputs/metrics/leakage_decisive.json`, 50 re-splits,
  seed 20260914, n = 29 decisions, 12 held out:

```
  contaminated vintage (OSHA bound)   9.24 of 12    sd 1.00
  honest vintage (stated date)        8.22 of 12    sd 1.04
  covariate removed                   4.48 of 12    sd 1.25
  share_of_covariate_value_retained   0.7857
```

  and `outputs/metrics/leakage_test.json` for the ablation that sets the
  stakes: removing the covariate costs **7.70 of 38** hits and loses **0 of
  50** re-splits.
- **The caveats are load-bearing and must travel with the number.** The
  artefact states them itself: n = 29 is 31% of the 94-decision working set
  (`n_decisions_lost` 65); the honest arm reads a **median two years older**
  vintage, so staleness and contamination are confounded and 21% is an
  **upper bound** on the leak; the intersection is not a random subsample.
  A model-free check agrees in mean and not in median: the chosen ZCTA gains
  **+1.04 warehouses** more than its metro rivals between vintages, but the
  median excess is **0.00** and only **11 of 29** facilities show any
  (`self_count_check`).

### G12. §5.8 Contributions omits the two that are actually novel

The four claims listed are all pre-expansion. Two things now exist that did
not, and both are stronger than anything in the current list:

1. **A measured visibility gap** — a direct count of how much of the
   operator's footprint is invisible in free public records, rather than a
   capture-recapture estimate of it. `nlrb_coverage.json` supplies the
   estimate side (OSHA sees at most 54% of cities); the MWPVL city list
   supplies the direct side. **See G18 — the direct count is not currently
   emitted to any artefact and cannot be quoted until it is.**
2. **A key covariate audited for circularity**, with a quantified answer
   (`leakage_decisive.json`). Very few applied papers test whether their
   headline predictor contains its own outcome. This one now does, and only
   because the opening dates exist.

### G13. §4.7 — "a convenience sample from an enforcement process"

Still true, and its *severity* has changed in a way the paragraph should
record. 596 of 700 panel rows now come from a source whose discovery
mechanism is a consultancy tracking permits and trade press — **not** an
enforcement process. The selection threat is not removed; it is replaced by a
different and partially independent one, which is a better position and a
different argument.

- **Settled by:** `mwpvl_merge.json` `expanded_panel.by_source_dataset`.

### G14. §1 "What changed from v4" and the Executive Summary

Both are the reader's map of the project and both stop on 2026-09-14 morning.
Neither mentions the extraction, the expansion, the refit or the leakage
audit. The Executive Summary's three contributions are the pre-expansion
three.

---

## 3. PENDING — blocked on ranked items 5 and 6

### G15. Every "104 facilities / 94 decisions" figure — PENDING: item 5

Appears at §3.1 (570-600), §3.2 (649, 660), §5.4 (1720-1734), §6-D (2224),
§6-M (2285), and in the Executive Summary (162-176).

**These are not wrong today.** The fitted model in `choice_report.json` is
genuinely on 94 decisions from the 104-row hand-verified
`national_facilities.csv`, and `warehouse/mwpvl_merge` writes the expanded
panel to a *new file beside it* rather than replacing it. What is wrong is
the impression that 104 is all there is.

A refit on the expanded frame already exists as an **experiment**:

```
  outputs/metrics/refit_expanded.json, 50 re-splits, seed 20260914
                        original_104        expanded (arm key "expanded_658")
  facilities loaded          100                     694
  decisions                   94                     485
  held out                    38                     194
  top-10 rate              0.5421                  0.5219
  Brier                    0.007550                0.005042
  beta warehousing   1.528 [0.985, 2.550]    1.170 [0.895, 1.455]
```

Interval width 1.5648 → 0.5602, a **64.2% narrowing**, and it **still spans
1.0**; the point estimate moved **toward** the numeraire. Two things must be
said with it or it will be misread:

- **Prediction did not improve.** Held-out top-10 rate fell very slightly
  (0.542 → 0.522) on a much larger and differently-composed test set.
- The arm key `expanded_658` is a **stale label** — the run loads 694
  facilities, not 658 (`AUDIT_2026_09_14.md` §6.2). Quote the field, never
  the key.

Until item 5 wires the expanded panel into `warehouse/facilities.attach`,
this is an experiment beside the pipeline rather than the project's headline,
and the document must say which it is quoting.

### G16. Market-size stratification — PENDING: item 5, and an artefact defect

The most interesting methodological finding of the expansion is that **pooled
top-k across heterogeneous choice sets is not an interpretable statistic**:
the expanded sample is weighted toward small markets where chance alone
already lands in the top ten ~67% of the time, so pooled lift measures the
mix of questions rather than the model.

It cannot be quoted yet, for two independent reasons:

1. `outputs/metrics/lift_by_market_size.json` **has no emitter**
   (`AUDIT_2026_09_14.md` §2.4) — five citations, zero writers, no `run_id`,
   no `written_at`, not regenerable by any code in the tree.
2. It **contradicts itself**. Its `finding` string says *"Pooled lift fell
   3.68x->2.61x"*; its own fields say `original.pooled_lift` 2.9480 and
   `expanded.pooled_lift` 2.7572. The small-market share in the same sentence
   (7% → 14%) does check out (0.0745 → 0.1361).

The *structure* of the finding is robust and is visible in the stratified
fields, which do agree with each other:

```
  large markets (>100 candidate ZCTAs)   original 6.14x  ->  expanded 6.42x
  mid    (26-100)                                 2.67x  ->          3.09x
  small  (<=25)                                   1.66x  ->          1.44x
  share of decisions that are small markets        7.4%  ->          13.6%
```

**Do not quote `../PROGRESS_2026_09_14.md`'s "6.37x -> 6.31x".** Those came
from `panel_experiments.json`, which was rewritten at 14:41 — after the memo
was written at 14:17 — and now reports 6.18 (arm `original_only`) → 6.33 (arm
`combined`) for the same statistic. That file is still being produced by
another agent. Mark any figure taken from it `[PENDING: item 5]`.

### G17. §6 defect F, "Every facility coordinate is empty" — PENDING: item 6

> *"Both panels are 0% populated on latitude and longitude … Geocoding the
> addresses is a day's work and is not done."*

True as written; 700 rows and 0 coordinates
(`mwpvl_merge.json.caveats[4]`). Geocoding is in flight as ranked item 6. The
count of addresses is now 700 rather than 104, and the sentence should say
so. The *result* of the geocoding is `[PENDING: item 6]` and must not be
anticipated.

### G18. The visibility-gap headline is not artefact-backed — quote nothing yet

`../PROGRESS_2026_09_14.md` §5 states: *"MWPVL names delivery stations in 420
US cities. The best free source, OSHA, sees 340 cities in total across all
Amazon facility types, overlapping on 106."*

Only one of those three numbers is currently in an artefact. `340` is
`nlrb_coverage.json` `national_two_list.n_osha`. **`420` and `106` appear
nowhere in `outputs/metrics/` or `docs/`** — verified by grep across both
trees. The framing is almost certainly right and the arithmetic is cheap, but
under this document's own citation rule the figure cannot enter the proposal
until something writes it down. Treat as `[PENDING: emitter]`, not as
`[PENDING: item 5]` — it needs about twenty lines of code, not the panel
rewire.

---

## 4. Artefact-level defects that constrain what the proposal may say

Recorded here because a writer working from this report will otherwise trip
over them. None is mine to fix; all are cited so the proposal quotes around
them.

| artefact | defect | reference |
|---|---|---|
| `lift_by_market_size.json` | no emitter; `finding` string contradicts own fields | audit §2.4 |
| `refit_expanded.json` | arm key `expanded_658` reports 694 facilities | audit §6.2 |
| `mwpvl_merge.json` `caveats` | still says *"Only 2 of MWPVL's 13 tables have been parsed"* and quotes 591 | audit §2.5 |
| `mwpvl_merge.json` `facility_check` | `passes: false` — 144 of 700 rows have a non-numeric `open_year` | the artefact itself |
| `panel_experiments.json` | rewritten 14:41, another agent is still working in it | mtime; audit |
| all sprint artefacts | no `run_id`, no `written_at`, so the "artefact wins" tie-break cannot be applied | audit §6.5 |
| 14 figures + both decks | all rendered 2026-09-13 09:36, before the OCR pipeline existed | audit §6.3 |

The last row is why phase 2 adds no new figure. Every figure showing a sample
size or a facility map is showing the 104-row world, and re-rendering is
downstream of item 5.

---

## 5. What a `.docx` rebuild would require

The Markdown is the source; `PROPOSAL_V5.docx` is a render of it. Nothing in
this report edits the `.docx`, and the inspirator has not approved rewriting
the submitted document.

**The toolchain is not the obstacle.** `.venv/bin/python` has `python-docx`
(`.venv/lib64/python3.13/site-packages/docx/`), and `build_v5.py` was run
against a throwaway `--out` to confirm it renders this Markdown cleanly:
1.7 MB, **8** figures embedded, exit 0. (Eight, not fourteen — v5 references
fig02, 03, 08, 09, 10, 11, 13 and 14; §8's figure rule removed four others.)
`README.md:52` writes the command as
`<docx python> tools/proposal/build_v5.py`, implying a separate interpreter
is needed; that hedge is out of date and the repo venv is sufficient.

Two things are genuinely required:

```
  1  EXPLICIT APPROVAL to overwrite docs/proposal/PROPOSAL_V5.docx
       The build has no --dry-run and writes in place.  The current .docx was
       built 2026-09-14 01:27 and is what an examiner would open.  This is
       the whole of the blocker.

  2  A DECISION ABOUT THE FIGURES, which is a content question, not a build
     one.  build_v5.py hard-fails if any referenced PNG is missing, by
     design, and all 8 referenced PNGs are present — the build succeeds.  But
     they
     were rendered 2026-09-13 09:36, before the OCR pipeline existed, so a
     rebuild today embeds pre-expansion figures in a post-expansion
     document.  Either accept that and caption it (§3.2 already carries a
     precedent caption doing exactly this for fig08), or re-render:
           .venv/bin/python tools/figures/build_all.py
     which is downstream of ranked item 5 and will not change anything
     useful until the expanded panel is wired in.
```

The command, once approved:

```
  .venv/bin/python tools/proposal/build_v5.py
  .venv/bin/python tools/docs/md_to_txt.py \
      docs/proposal/PROPOSAL_V5.md docs/proposal/PROPOSAL_V5.txt --width 0
```

Note the `--width 0`. `PROPOSAL_V5.txt` is rendered unwrapped so paragraphs
reflow in Word; every other doc in the tree uses `--width 80`, and using the
wrong one produces a large spurious diff (`README.md:57-60`).

Word builds the table of contents from the heading styles and `build_v5.py`
does not insert one — the script prints that reminder on every run.

---

## 6. Build-pipeline fix made in phase 1

`scripts/build_all.sh:21` ran `tools/proposal/build_v4.py`, so `make docs`
regenerated the **superseded** v4 document and never touched v5
(`AUDIT_2026_09_14.md` §2.7). Verified before changing: `build_v5.py` renders
`PROPOSAL_V5.md` to `PROPOSAL_V5.docx` and is the current deliverable's
builder; `grep -n build_v5 scripts/ Makefile` returned nothing.

The script now builds v5 and no longer builds v4. v4 is documented as
HISTORICAL in `README.md:12-16`; regenerating a historical document on every
`make docs` is how the stale artefact stayed in the build in the first place.

**The script was not run.** Running it would overwrite `PROPOSAL_V5.docx`,
which §5 above says requires approval. `build_v5.py` *was* run once against a
throwaway `--out` to confirm the edited Markdown still renders.

---

## 7. What was actually changed, 2026-09-14

### Phase 1 — the WRONG class, and the build target

| gap | where | change |
|---|---|---|
| G1 | §2.2 | "We decline to buy the same panel" replaced; free article vs commercial panel distinguished, with a dated correction block |
| G2 | §4.3 | failed-routes row relabelled "a 2012 industry snapshot (the WRONG document)" and told to see below |
| G3 | §4.3 | WORKED block split into WORKED (1) OSHA / WORKED (2) MWPVL OCR, with the extraction counts |
| G4 | §4.3 | "decided not to buy" rewritten: refusal retained, consequence corrected, the publisher's withdrawal quote added, and the un-archived source stated as an open defect |
| G5 | §3.2 | "the benchmark was never fitted" replaced with the fitted result and the ceiling reading |
| G6 | §3.2 | criteria table "MET, AND IT WINS" → "MET, AND IT DRAWS", with the margin |
| G7 | §5.4, §6-M | "on the only evidence available" (n=5) replaced with n=42 and the 34-month median |
| G8 | §9 | GBM timeline row "NOT YET BUILT" → DONE, with the result |
| G9 | §3.3 | coverage artefacts now quoted; MWPVL added as a legitimate fourth list; 209 → 208 corrected to the artefact |
| §2.7 | `scripts/build_all.sh:21` | `build_v4.py` → `build_v5.py`, with a comment saying why |

### Phase 2 — the MISSING class

Two new sections, both appended at the end of their parents so that **nothing
was renumbered** and no cross-reference in the document or the tree broke:

```
  4.8   The opening dates, recovered
          4.8.1  what was read, and why plain OCR was abandoned
          4.8.2  three independent validations
          4.8.3  what entered the panel, and the filter that is the headline
  5.10  The expanded panel, and what quintupling the sample bought
          5.10.1  the headline, stated before the detail
          5.10.2  an aggregation artefact          [PENDING: item 5]
          5.10.3  the audit the new dates made possible
          5.10.4  two independent lines, one ceiling
```

Plus: a dated block at the end of §1; a paragraph in the Executive Summary;
contributions 5 and 6 in §5.8 (and its "Four claims" → "Six claims"); a
`[PENDING: item 5]` block under §3.1's arithmetic; §4.7's selection-threat
paragraph extended; §6 defect F updated to 700 addresses with
`[PENDING: item 6]`; §6 defect M marked PART-CLOSED; §6 defect O's clause about
blocking E and M withdrawn; four new timeline rows and three revised ones.

### Three `[PENDING]` markers are live in the document

```
  §3.1, §5.10.2  [PENDING: item 5]   expanded panel -> warehouse
  §4.8.3, §6-F   [PENDING: item 6]   geocoding of the 700 addresses
  §5.8, §5.10.4  [PENDING: emitter]  visibility count; land-use run
```

None of them guesses at a figure. Removing a marker requires the artefact, not
a decision.

### Not changed, deliberately

- **No `.docx`, no `.pptx`, no figure.** §5 above.
- **No renumbering.** §4.8 and §5.10 sit at the ends of their sections for this
  reason; it is uglier than inserting them in narrative order and it is the
  only way to add ~450 lines to a cross-referenced document without a sweep.
- **Nothing outside `docs/proposal/` and `scripts/build_all.sh`.** In
  particular no artefact was regenerated and no number was recomputed: every
  figure quoted was read from an existing file under `outputs/metrics/`, or —
  in the two cases where no artefact exists (the 0-of-40 cost-rank finding and
  the n=42 date-gap distribution) — from the named document, with that fact
  stated in the text.
