# Figures — index

*Index last updated 2026-09-16, re-derived from what is actually on disk.
Previously 2026-09-13, after figs 08 and 09 were rebuilt from measured
artefacts.*

**Fourteen PNGs are in this directory, from three separate builders, and five
more are described here but not on disk.** The counts are worth setting out,
because "the 14 figures" used to mean fig01-fig14 and now collides with a
different 14:

```
  on disk (14)          fig01 fig02 fig03 fig04 fig05 fig06 fig07 fig08 fig09
                        hero_cost_per_parcel
                        fig_metro_auc  fig_dispersion  fig_visibility_gap
                        fig_cost_by_metro
  described, absent (5) fig10 fig11 fig12 fig13 fig14
```

Three builders, and they do not know about each other:

| builder | writes | consumed by |
|---|---|---|
| `tools/figures/build_all.py` | `fig01`–`fig14` | the proposal docx and both decks |
| `tools/figures/fig_hero_cost.py` | `hero_cost_per_parcel` | the top-level `README.md` |
| `tools/figures/fig_paper.py` | the four `fig_*` results figures | `paper/siting_atlas_ieee.tex` |

`tools/figures/build_all.py` still declares and builds all fourteen numbered
figures; figs 10-14 simply were not written in the 2026-09-15 16:22 rebuild
that produced the nine that are here. **Until `build_all.py` is re-run,
`tools/proposal/build_v4.py` will hard-fail** — its `REQUIRED_FIGURES` list
names all fourteen and `check_figures` refuses to assemble the document with
any of them missing. `tools/deck/build_deck.py` needs fig10-fig14 too. Nothing
is lost; they are regenerable by one command. The entries for figs 10-14 below
describe what that command will produce.

`hero_cost_per_parcel` and the four `fig_*` paper figures were not indexed
here at all until 2026-09-16. None of the five is part of the numbered
fourteen.

**Every one of them is generated. Do not edit a PNG; edit the Python that
draws it and rebuild.**

**Seven of the fourteen on disk contain measured results**, and they are the
ones to trust. `fig08_backtest` and `fig09_conformal_coverage` read every
value they print from
`experiments/hazard-model/artefacts/hazard_report.json` at build time and
carry the run id on the image. `hero_cost_per_parcel` and `fig_cost_by_metro`
read every value they plot from
`outputs/tables/cost_to_serve_2023q4_baseline.parquet`; `fig_metro_auc` from
`metro_entry.json`, `fig_dispersion` from `gravity_network.json`,
`fig_visibility_gap` from `mwpvl_coverage.json`. The other seven — fig01
through fig07 — are schematics or hand-typed illustrative numbers
(`fig06_portfolio` is part live; its ZCTA count comes from `scope.json`).
fig08 and fig09 were both previously hand-typed illustrations and both were
wrong; see "What was fixed" below. Read "What is stale" before you put any of
the schematics in front of an examiner.

---

## How they are built

```
  python tools/figures/build_all.py            # writes fig01-fig14 into
                                               # docs/figures. Run this first:
                                               # fig10-fig14 are missing today
  python tools/figures/fig_hero_cost.py        # writes hero_cost_per_parcel.png
                                               # -- NOT registered in build_all
  python tools/figures/fig_paper.py            # writes the four fig_*.png the
                                               # IEEE paper embeds -- also NOT
                                               # registered in build_all
  bash   scripts/build_all.sh                  # step 1/4 calls build_all.py,
                                               # then rebuilds docx and both
                                               # decks
  make docs                                    # calls scripts/build_all.sh
```

`make figures` is a **different** target. It runs `python -m siting_atlas.viz.build`
and writes the ~20 genuinely data-driven cost charts into `outputs/figures/`
(`cost_vs_density_*`, `cost_by_metro_*`, `cost_decomposition_*`,
`cumulative_coverage_*`). If you want a chart that came from the pipeline, look
there, not here.

The drawing code:

```
  tools/figures/build_all.py        the driver
  tools/figures/common.py           palette, box primitives, text auto-fit
  tools/figures/fig_architecture.py figs 01-03
  tools/figures/fig_methods.py      figs 04-07
  tools/figures/fig_evaluation.py   figs 10, 14
  tools/figures/fig_backtest.py     figs 08, 09 -- the measured ones
  tools/figures/fig_impact.py       figs 11, 12, 13
  tools/figures/fig_hero_cost.py    hero_cost_per_parcel -- standalone, NOT
                                    in build_all.py's MODULES list. Reads
                                    outputs/tables/cost_to_serve_2023q4_
                                    baseline.parquet and types nothing
  tools/figures/fig_paper.py        the four paper figures -- also standalone
                                    and not in MODULES. Every value read from
                                    an artefact at build time
  tools/figures/figbase.py          IEEE column geometry, palette and the
                                    minimum-point-size gate fig_paper.py puts
                                    each figure through before writing it
  tools/scope.py                    live data hook: reads
                                    outputs/metrics/scope.json, used by
                                    fig06 and fig12 for scope counts
  tools/hazard_metrics.py           live data hook: reads
                                    experiments/hazard-model/artefacts/hazard_report.json, used
                                    by fig08 and fig09 and by the proposal
                                    and deck builders. Raises at import if
                                    the artefact is missing, so a figure
                                    cannot be drawn with an invented number
```

`tools/proposal/build_v4.py` hard-fails if any of the 14 is missing, so a
deleted PNG breaks the proposal build rather than producing a silent hole.
**It will hard-fail right now**, on fig10 through fig14 — which is the check
doing its job, not a defect.

---

## The figures

`SCHEMATIC` = a diagram, no numbers to be wrong about. `ILLUSTRATIVE` = the
numbers in the picture are typed into the source by hand and are **not
results**. `PART LIVE` = some values come from `outputs/metrics/scope.json`.
`ABSENT` = described here and buildable, but not on disk today.

```
  fig01_architecture     End-to-end flow: 8 public sources -> ELT/DuckDB ->
                         models -> decision layer -> agent -> app.
                         SCHEMATIC. Hard-codes "SITING / TIMING MODEL:
                         discrete-time hazard" in the contribution box —
                         wrong the moment the ZIP-choice model lands.

  fig02_star_schema      Kimball star: fact_siting_economics plus five
                         dimensions, and why dim_scenario exists.
                         SCHEMATIC. Column lists are typed by hand, not read
                         from the real DuckDB schema, so they can drift.

  fig03_agent_gates      The ReAct THOUGHT/ACTION/OBSERVATION loop, three MCP
                         tools, the six-gate mutation path, the HITL box.
                         SCHEMATIC. Still accurate; the agent gates are one
                         of the four components that work.

  fig04_estimand         The circularity trap (constructed ZINB target,
                         "MAPE 3-5%" as proof of the loop) against the
                         observable outcome that replaces it.
                         SCHEMATIC, STALE. The right-hand box says
                         "DISCRETE-TIME HAZARD MODEL" and lists AUC / PR-AUC
                         / Brier / ECE / precision@k. Both halves are
                         superseded — see below.

  fig05_decay            Cannibalisation decay against distance with a 95%
                         band, -12.1% at 2 km fading to non-significant at
                         26 km, and the spatial weight matrix it implies.
                         ILLUSTRATIVE. The curve is four literal numpy
                         arrays. Nothing was estimated. This estimand has
                         never been touched.

  fig06_portfolio        Why ranking misses profitable bundles: ZIP A -$0.20M,
                         ZIP B -$0.15M, A+B together +$1.10M.
                         ILLUSTRATIVE bars; PART LIVE — the ZCTA count and
                         the 2^2,413 search space come from scope.json.
                         The ARGUMENT is sound and the real optimiser does
                         run; the three bar values are made up.

  fig07_tornado          Capital-bucket sensitivity across eight buckets,
                         swing +/-$0.10M to +/-$1.34M, four buckets carrying
                         ~75% of it.
                         ILLUSTRATIVE. Does NOT read
                         outputs/metrics/cost_report.json, which exists.
                         Low-effort, high-value fix: wire it up.

  fig08_backtest         Three panels on the measured backtest: AUC against
                         a 0.5000 null, Brier score against a constant on
                         the same rows, and the ten-bin calibration curve
                         against the 45-degree line.
                         LIVE. Every number is read from
                         experiments/hazard-model/artefacts/hazard_report.json and the run id is
                         printed on the image. It shows a model that failed,
                         which is the project's central finding.

  fig09_conformal_coverage
                         Split conformal prediction: measured coverage
                         (88.19%) against nominal (90%) inside the two-sigma
                         band that 351 independent units allow, and the
                         composition of the prediction sets — 89.91% one
                         label, 10.09% EMPTY, 0.00% both.
                         LIVE. Replaced fig09_rank_stability, which invented
                         eight ZIP codes and their shares of a Monte Carlo
                         pass that has never been run.

  hero_cost_per_parcel   The repository's hero image: median and
                         interquartile cost to deliver one parcel, for each
                         of the 10 pilot metros, ranked, with the national
                         median as a reference line.
                         LIVE, and the only figure here that reads the COST
                         model rather than the hazard model. Every value --
                         the ten medians, the IQR whiskers, the national
                         median, the "2,333 ZIP code areas in 10 metros"
                         subtitle -- is computed at build time from
                         outputs/tables/cost_to_serve_2023q4_baseline.parquet.
                         Miami cheapest at $0.94, Boise dearest at $1.43.
                         Draws the IQR and not p10-p90 on purpose: Boise's
                         p90 is $3.56 against its own median of $1.43, and
                         plotting it flattens the other nine metros. The
                         source docstring records that choice.
                         Not one of the fourteen; not embedded in the
                         proposal or either deck; used as the README image.

  fig_metro_auc          Out-of-time AUC by held-out year, model against the
                         households baseline, verdict arm `prereg_strict`,
                         form `logit`.
                         LIVE, from outputs/metrics/metro_entry.json. Draws
                         the run id. Paper Fig. 2.

  fig_dispersion         Within-metro cv against interior/boundary for the 21
                         network terms, log x-axis, with the empty 0.6-1.3
                         band shaded. Hollow markers are terms interior in
                         one arm and boundary-straddling in another.
                         LIVE, from experiments/gravity-network/artefacts/
                         gravity_network.json. Its own subtitle states the
                         one-way reading — "Low variation guarantees failure.
                         High variation guarantees nothing." Paper Fig. 3.

  fig_visibility_gap     One stacked bar: 138 of 488 delivery-station cities
                         with an OSHA record, 350 invisible.
                         LIVE, from outputs/metrics/mwpvl_coverage.json
                         (unstamped artefact — mtime only). Paper Fig. 1.

  fig_cost_by_metro      The same data as hero_cost_per_parcel, redrawn at
                         3.40in for an IEEE column: median and IQR cost per
                         parcel by metro, national median as a reference
                         line, "San Francisco Bay Area" shortened because the
                         geometry gate rejected the full label at that width.
                         LIVE, from the cost parquet. Paper Fig. 4.

  The four above are paper-only: tools/figures/fig_paper.py writes them,
  paper/siting_atlas_ieee.tex embeds them, and neither build_all.py nor the
  proposal nor the decks know they exist. They are each drawn AT the width
  they will be placed at, so nothing scales them; figbase.py refuses to write
  a figure whose text would land below 6.5pt on the page.

  ------------------------------------------------------------------------
  The five below are ABSENT from docs/figures as of 2026-09-16. They are
  declared in tools/figures/build_all.py and rebuild in seconds. The
  descriptions are of what the code draws.
  ------------------------------------------------------------------------

  fig10_positioning      What the literature already owns and what is left to
                         claim, after the prior-art check; plus the rule
                         never to write "first" or "novel".
                         SCHEMATIC / text. Current, and consistent with the
                         three withdrawn novelty claims in
                         ../proposal/CHANGELOG.txt.

  fig11_stakeholders     Who makes a different decision because this exists:
                         planners and air districts, EJ groups, competing
                         operators, researchers; plus the killer question and
                         the explainability-ceiling box.
                         SCHEMATIC / text. Current.

  fig12_scale            "Row count is the only axis where this is small":
                         1,081,312 rows / 15 MB reframed as 2,413 markets at
                         $3-5M each, then a seven-axis relative-magnitude bar
                         chart.
                         PART LIVE — rows, MB, ZCTAs, capital, draws and
                         search space come from scope.json. The bar LENGTHS
                         are invented and the axis label admits it. Two
                         defects, below.

  fig13_currency         Data currency: eight sources ranked by reporting lag
                         (ACS 5-year at 21 months down to Zillow at 1 month)
                         against an 18-36 month decision lead band, and why a
                         lagged covariate is the right covariate.
                         ILLUSTRATIVE. The lags are typed from source
                         documentation rather than measured by the ingest
                         layer, so they can silently go out of date. Compare
                         against the measured column in ../data/README.md.

  fig14_market           Six-row competitive table — Esri, Buxton/Placer,
                         Coupa/AIMMS, consultancies, operator-internal,
                         academia — and the gap none of them fills.
                         SCHEMATIC / text. Current.
```

---

## Start here

If you are preparing to present: open `fig08_backtest.png` first, because it
is embedded in the proposal as Figure 4 and in both decks and it is the figure
most likely to be challenged. It now shows the measured failure rather than a
target, so the challenge to prepare for is "why is this in your deck at all",
and the answer is in `../METHODS_RESEARCH.md` §14.4.

If you are trying to understand the project: `fig01_architecture` then
`fig04_estimand`, in that order, keeping in mind that both name the abandoned
hazard model.

---

## What was fixed, 2026-09-13

### fig08_backtest printed a result the project does not have

The figure printed AUC 0.84, PR-AUC 0.31, Brier 0.048, ECE 0.03,
precision@100 0.61 and "conformal 90% intervals covered 90.2%" — pre-registered
targets, drawn as though measured. Its ROC curve was not a curve at all: it was
`tpr = fpr ** (1/0.84 - 1)`, chosen so that the area under it would equal the
0.84 printed beside it. The source comment said as much.

What it prints now, all of it read from
`experiments/hazard-model/artefacts/hazard_report.json`:

```
                        was (typed)   now (measured)   null (a constant)
  AUC, units held out   0.84          0.6894           0.5000
  AUC, time held out    --            0.5551           0.5000
  Brier, units          0.048         0.019522         0.019614
  Brier, time           --            0.020635         0.020213
  ECE, units            0.03          0.00863          0.00005
  precision@100         0.61          never computed   --
  conformal coverage    90.2%         88.19%           nominal 90%
```

Three notes on reading that table, because earlier versions of this file got
each of them wrong.

**The Brier pair is the headline, not the AUC.** Both numbers in a row are over
the same 8,044 rows. Report the raw pair and not the skill score: Gneiting and
Raftery (2007) §2.3 p.362 state that skill scores are generally improper even
when the underlying rule is proper.

**"Out-of-time AUC 0.5551, below the base rate" — which an earlier version of
this file said — is wrong twice.** AUC's null is 0.5000, not the base rate of
0.0200; the two are not on the same scale and the comparison is meaningless.
0.5551 is slightly *above* its null, not below anything.

**The geographic hold-out is deliberately not in the table.**
`experiments/hazard-model/artefacts/hazard_report.json:819` records that Phoenix and Boise hold
two dated stations between them, "so this is a smoke test for gross failure
and not a test of geographic transfer". Quoting its -0.0618 as a transfer
result overstates the evidence against the project's own model.

### fig09_rank_stability invented eight ZIP codes

It showed 94608, 94501, 98108, 60632, 78745, 94612, 11208 and 30318 holding a
top-ten position in 87% down to 16% of "10,000 Monte Carlo draws". The ZIPs
were invented, the shares were invented, and the Monte Carlo pass has never
been run. Unlike fig08 it carried no on-figure caveat at all.

It has been deleted and replaced by `fig09_conformal_coverage`, which occupies
the same slot in the proposal — the uncertainty a recommendation carries — with
an analysis that exists. The proposal text around it now states in terms that
the rank-stability pass has not been run and that no rank-stability figure is
quoted anywhere in the document.

### What the fix touched

```
  tools/hazard_metrics.py                NEW. Reads hazard_report.json;
                                         raises at import if it is missing
  tools/figures/fig_backtest.py          NEW. figs 08 and 09
  tools/figures/fig_evaluation.py        figs 08/09 removed; 10 and 14 remain
  tools/figures/build_all.py             registers the new module
  tools/proposal/build_v4.py             REQUIRED_FIGURES renamed fig09
  tools/proposal/sections_core.py        Figure 4 caption; a callout stating
                                         the criteria were missed; the
                                         label-noise example no longer quotes
                                         an AUC of 0.84
  tools/proposal/sections_methods.py     Figure 11 replaced; rank-stability
                                         callout marked not-run; §5.5 no
                                         longer claims a precomputed
                                         drive-time matrix
  tools/deck/slides_story.py             v1 s12 and s13
  tools/deck/notes_v1.py                 v1 presenter notes 12 and 13, with
                                         measured figures substituted rather
                                         than typed
  tools/deck/slides_v2_results.py        v2 s17 and s18
  tools/deck/notes_v2.py                 v2 presenter note 18
```

The same 0.84 / 0.61 pair was also a CV bullet in
`../career/PORTFOLIO_PLAYBOOK.md`, and has been rewritten. See that folder's
README.

---

## What is stale

### fig04_estimand endorses the abandoned specification

It is not false — it shows no results — but the box it points at says
"DISCRETE-TIME HAZARD MODEL", and `../METHODS_RESEARCH.md` §14.3 records that
the unit moved
from ZCTA-quarter to the station siting decision and the headline metric moved
from AUC to Brier skill plus calibration. The metric list in the figure no
longer matches the specification. It needs redrawing for the conditional ZIP-choice
model. `fig01_architecture` has the same string in its contribution box.

### fig12 has two concrete defects

```
  1  It reads $7.2B-$12.1B correctly from scope.json, then hard-codes the
     string "national, if scaled: $99B - $165B" on the next line, while
     scope.json says "$101B-$169B". SCOPE.capital_national exists and is
     unused. This is exactly the class of drift tools/scope.py was written
     to prevent.
  2  The rendered PNG loses its dollar signs. "$7.2B-$12.1B" opens matplotlib
     mathtext at the first "$", so the headline currency figure renders as
     italic maths: "= 7.2B - 12.1B". Escape the dollars or use a raw string.
```

### fig05's deck slide claimed a result it does not have — corrected

The figure itself was always labelled illustrative, and the Word caption says
"Values are illustrative pending estimation". The v1 deck did not. Slide 8 was
titled *"Idea 1, measured"* and its presenter note instructed the speaker to
"read the one-line result aloud: minus 12 percent within 8 km, minus 4 at 8 to
20, indistinguishable from zero beyond 20", followed by "nobody has published
that number". Nobody has published it because nobody has estimated it,
including us. The slide title, subtitle and note now say so, and the note tells
the speaker not to read a number off the slide. The figure is unchanged,
because there is nothing to regenerate it from.

### fig05 and fig07 are cheap to make real

fig07 could read `outputs/metrics/cost_report.json` today and become a genuine
sensitivity analysis. fig05 cannot — the cannibalisation decay has never been
estimated, and `../ROADMAP.md` "Phase 3 — Causal layer" lists the spatial-DiD
estimand as never started.
Until it is, fig05 is a picture of a hypothesis.

---

## Where they are used

Nothing in Markdown references these PNGs. They are consumed only by the
document builders.

```
  Proposal (Word), tools/proposal/build_v4.py — all 14, in this order:
    Fig 1  fig11   Fig 2  fig10   Fig 3  fig14   Fig 4  fig08
    Fig 5  fig13   Fig 6  fig04   Fig 7  fig01   Fig 8  fig02
    Fig 9  fig05   Fig 10 fig07   Fig 11 fig09   Fig 12 fig06
                                         (fig09_conformal_coverage)
    Fig 13 fig03   Fig 14 fig12

  Decks, tools/deck/build_deck.py — 9 of the 14:
    fig01 03 05 08 10 11 12 13 14
    fig02, 04, 06, 07, 09 are proposal-only

  hero_cost_per_parcel — neither builder. It is embedded by the top-level
    ../../README.md and listed in ../../paper/README.md; it is the
    repository's cover image.

  Paper, paper/siting_atlas_ieee.tex — the four fig_* figures only:
    Fig. 1 fig_visibility_gap   Fig. 2 fig_metro_auc
    Fig. 3 fig_dispersion       Fig. 4 fig_cost_by_metro
    It reaches them through \graphicspath and uses none of fig01-fig14.
```

*(The line above this block used to read "Nothing in Markdown references these
PNGs." That is still true of fig01-fig14 and was never true of the hero.)*

There is no `.txt` twin convention here; these are binaries, not documents.
