# The figure layer: what draws what, and what each one depends on

*Compiled 2026-09-15 by reading the code and stat-ing the artefacts. Every
dependency below was confirmed by following the import, not by reading a
docstring.*

## There are two figure sets, not one

| set | count | drawn by | built | embedded in |
|---|---|---|---|---|
| `outputs/figures/` | 20 | `src/siting_atlas/viz/` | `python -m siting_atlas.viz.build --all-scenarios` | **nothing** |
| `docs/figures/` | 14 | `tools/figures/` | `python tools/figures/build_all.py` | all 14 in the proposal |

These are commonly conflated. They share no code, no style module and no
build command. `outputs/figures/` is the cost-model batch output and the
batch twin of the Streamlit dashboard; `docs/figures/` is the proposal
figure set. `fig08_backtest` and `fig09_conformal_coverage` are in the
second set, not the first.

---

## Set 1 — `outputs/figures/`, 20 PNGs

Four chart families x five cost scenarios (`baseline`, `congested`,
`dense_routing`, `high_fuel`, `pessimistic_tour`).

| chart | function | reads |
|---|---|---|
| `cost_vs_density_2023q4_<scenario>` | `viz.charts_density.cost_vs_density` | `outputs/tables/cost_to_serve_2023q4_<scenario>.parquet` |
| `cost_by_metro_2023q4_<scenario>` | `viz.charts_density.cost_by_metro` | same |
| `cost_decomposition_2023q4_<scenario>` | `viz.charts_economics.cost_decomposition` | same |
| `cumulative_coverage_2023q4_<scenario>` | `viz.charts_economics.cumulative_coverage` | same |

All twenty go through `viz.data.load`, which reads exactly one parquet and
checks 15 required columns. Nothing else is read.

**Facility-panel dependency: none.** The chain is
`cost.runner` -> `data/processed/panel.parquet`, but `cost/runner.py:30`
takes only `households, median_household_income, land_area_sqmi, latitude,
longitude, wage_light_truck_driver, diesel_usd_gal, population, cbsa_code`
plus `zcta`. It never reads `enabled` and never touches a facility table.
The 104 -> 693 facility expansion cannot move these figures. They move only
if ACS/BLS/EIA columns move or `cost/params.py` moves.

---

## Set 2 — `docs/figures/`, 14 PNGs

Only four of the fourteen read a measured artefact. The rest are diagrams
and illustrations with their numbers written in the source.

| figure | module | artefact | facility-panel dependent |
|---|---|---|---|
| `fig01_architecture` | `fig_architecture` | none (diagram) | no |
| `fig02_star_schema` | `fig_architecture` | none (diagram) | no |
| `fig03_agent_gates` | `fig_architecture` | none (diagram) | no |
| `fig04_estimand` | `fig_methods` | none (diagram) | no |
| `fig05_decay` | `fig_methods` | **none — values hard-coded** | no |
| `fig06_portfolio` | `fig_methods` | `scope.json` via `tools/scope.py` | no (geography only) |
| `fig07_tornado` | `fig_methods` | **none — values hard-coded** | no |
| `fig08_backtest` | `fig_backtest` | `hazard_report.json` via `tools/hazard_metrics.py` | **yes** |
| `fig09_conformal_coverage` | `fig_backtest` | `hazard_report.json` | **yes** |
| `fig10_positioning` | `fig_evaluation` | none (diagram) | no |
| `fig11_stakeholders` | `fig_impact` | none (diagram) | no |
| `fig12_scale` | `fig_impact` | `scope.json` | no (geography only) |
| `fig13_currency` | `fig_impact` | none (diagram) | no |
| `fig14_market` | `fig_evaluation` | none (diagram) | no |

`scope.json` carries ZCTA and metro counts and a capital envelope, not
facility counts, so `fig06` and `fig12` are unaffected by the expansion.

**No figure in either set plots choice-model performance.** No figure draws a
top-k rate, a lift, or anything stratified or poolable by market size.

---

## The two traps, checked

`docs/research/COVARIATES_TRIED.md` §0 names two errors. Neither is committed
in the form described, but one near-relative is worse.

### Pooled top-k / lift across market sizes — not committed

No figure plots top-k or lift at all. The pooled numbers exist in the
artefacts (`refit_expanded.json` reports `top10_rate` 0.5196 against
`top10_uniform_rate` 0.1937, pooled across market sizes, for the 483-decision
`expanded_658` arm), and `lift_by_market_size.json` is itself marked
SUPERSEDED for exactly this reason — it is retired and unregenerable, with no
emitter anywhere in the tree, so nothing new should read it. Anything new that plots those fields must stratify or restrict
to large metros and say so on the figure.

### Re-split spread drawn as a confidence interval — not committed literally

`fig09` is the only figure with a band, and its footer says so in as many
words: *"The band in panel A is that two-sigma spread, not a confidence
interval."* That is correct practice.

### An *invented* interval — found 2026-09-15, fixed the same day

> **Status: FIXED.** This section is kept because the defect is instructive
> and because deleting the record of an error found in self-audit converts it
> into ordinary competence. What follows is what *was* committed, in the past
> tense, followed by the remedy. Neither figure carries the defect now.

`fig05_decay` hard-coded nine effect values and a band:

```python
eff = np.array([-12.1, -9.4, -6.2, -4.1, -2.3, -0.9, -0.4, -0.2, 0.1])
lo  = eff - np.array([2.2, 2.0, 1.9, 1.8, 1.7, 1.7, 1.6, 1.6, 1.6])
...
ax.fill_between(d, lo, hi, ..., label="95% CI")
```

and annotated one point `"-0.4%  n.s."`. The legend claimed a 95% confidence
interval and the annotation claimed a significance test, **on numbers that
were typed**. No cannibalisation regression had been run — and the outcome on
the y-axis, 2-day order volume, does not exist anywhere in this project's
data, which is precisely why that analysis was abandoned. The proposal caption
disclosed it ("Values are illustrative pending estimation"), but the figure
carried no mark of its own and figures are lifted into slides without their
captions.

`fig07_tornado` hard-coded eight bucket swings with **no** disclosure at all —
its caption asserted "Four primary buckets account for roughly three-quarters
of the swing in net present value" as measured fact. No artefact supports it:
`montecarlo_report.json` holds aggregate bands only, with no per-bucket
decomposition, so it cannot be redrawn from data.

**The remedy, and why it is not "we removed the numbers".** Neither figure
could be wired to an artefact, because for `fig05` the quantity does not
exist and for `fig07` the decomposition was never computed. Wiring was not
available, so both were **de-quantified** instead:

- the confidence band and the `"n.s."` annotation are gone;
- `ax.set_yticklabels([])` — the axis carries no numbers, because none of them
  is measured;
- an **in-axes** banner reads `ILLUSTRATIVE ONLY -- NO REGRESSION HAS BEEN
  RUN`, in red, inside the plotting area so that it travels with the image
  when the image is pasted into a deck without its caption;
- `fig07` received the same treatment: per-bar dollar labels removed, x-ticks
  removed, the same banner added.

The pedagogical point each figure existed for — that a decay curve is what
defines the cannibalisation radius, and which parameters dominate the spread —
survives without a single quantitative claim.

**The rule that came out of it** is in `tools/figures/fig_paper.py`: a figure
either reads every value from an artefact at build time, or it carries no
numbers at all. There is no third option. Of the fourteen figures, four now
read from artefacts and these two carry none.

This was the same defect class that `fig_backtest.py`'s docstring records as
having been purged from `fig08` and `fig09` ("hand-typed illustrations ...
drawn as though measured"). It recurred because the rule lived in one
module's docstring rather than anywhere enforceable.

---

## Measured provenance of the spread-vs-interval demonstration

Recomputed 2026-09-15 from `experiments/gravity-network/artefacts/network_inference.json`, arm
`combined_plus_network` (483 decisions, 194 metros), comparing the
Liang-Zeger CR0 metro-clustered CI width against the 50-re-split
2.5-97.5 percentile width:

```
  establishments               1.242x wider
  warehousing_establishments   0.954x  <- NARROWER
  sortation_proximity          1.399x
  fulfilment_proximity         1.479x
  --------------------------------------
  mean 1.268    median 1.320
```

The clustered interval is roughly **27-32% wider** on average, not 13%. A 13%
figure quoted anywhere should be traced or dropped. **The direction is no
longer uniform, which is a change from what this section used to say:** on
`warehousing_establishments` — the one parameter the headline rests on — the
clustered interval is 5% *narrower* than the re-split spread, so "the spread
understates the interval" cannot be stated as a rule. Note also that
clustering over metros gives *narrower* intervals than clustering over
decisions (ratios 0.73-0.97), so metro-clustering is not the conservative
choice by default.

`network_inference.json` carries `run_id 20260915-210640-dbcd`,
`written_at 2026-09-15T21:21:38+00:00`.

---

## Build commands

```bash
# set 1 (all 20)
PYTHONPATH=src .venv/bin/python -m siting_atlas.viz.build --all-scenarios

# set 2 (all 14)
.venv/bin/python tools/figures/build_all.py            # -> docs/figures
.venv/bin/python tools/figures/build_all.py --out DIR  # dry run elsewhere
```

`viz.build` overwrites `outputs/metrics/viz_report.json` as a side effect.
`build_all.py` returns 0 even when it reports a label overflow; only
`viz.build` fails the build on overflow.
