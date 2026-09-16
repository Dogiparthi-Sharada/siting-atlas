# Figures — index

*Index last updated 2026-09-13, after figs 08 and 09 were rebuilt from
measured artefacts.*

The 14 PNGs embedded in the proposal and the two decks. **Every one of them is
generated. Do not edit a PNG; edit the Python that draws it and rebuild.**

**12 of the 14 contain no real results.** They are schematics or hand-typed
illustrative numbers. The two that do — `fig08_backtest` and
`fig09_conformal_coverage` — read every value they print from
`outputs/metrics/hazard_report.json` at build time and carry the run id on the
image. Both were previously hand-typed illustrations and both were wrong; see
"What was fixed" below. Read "What is stale" before you put any of the other
twelve in front of an examiner.

---

## How they are built

```
  python tools/figures/build_all.py            # writes all 14 into docs/figures
  bash   scripts/build_all.sh                  # step 1/4 does the same, then
                                               # rebuilds docx and both decks
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
  tools/scope.py                    live data hook: reads
                                    outputs/metrics/scope.json, used by
                                    fig06 and fig12 for scope counts
  tools/hazard_metrics.py           live data hook: reads
                                    outputs/metrics/hazard_report.json, used
                                    by fig08 and fig09 and by the proposal
                                    and deck builders. Raises at import if
                                    the artefact is missing, so a figure
                                    cannot be drawn with an invented number
```

`tools/proposal/build_v4.py` hard-fails if any of the 14 is missing, so a
deleted PNG breaks the proposal build rather than producing a silent hole.

---

## The 14 figures

`SCHEMATIC` = a diagram, no numbers to be wrong about. `ILLUSTRATIVE` = the
numbers in the picture are typed into the source by hand and are **not
results**. `PART LIVE` = some values come from `outputs/metrics/scope.json`.

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
                         outputs/metrics/hazard_report.json and the run id is
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
and the answer is in `../PLAN.md` §9.

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
`outputs/metrics/hazard_report.json`:

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
`outputs/metrics/hazard_report.json:819` records that Phoenix and Boise hold
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
"DISCRETE-TIME HAZARD MODEL", and `../PLAN.md` §5 records that the unit moved
from ZCTA-quarter to the station siting decision and the headline metric moved
from AUC to Brier skill plus calibration. The metric list in the figure no
longer matches the plan. It needs redrawing for the conditional ZIP-choice
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
estimated, and `../PLAN.md` §6 lists the spatial-DiD estimand as untouched.
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
```

There is no `.txt` twin convention here; these are binaries, not documents.
