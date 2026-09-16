# Notes — the catchment radius, and the band it has needed since day one

*Built and run 2026-09-14. Artefact: `outputs/metrics/catchment_band.json`.
Code: `src/siting_atlas/warehouse/catchment_band.py`. Every number below is
read out of that artefact or measured by a command printed beside it. None is
recalled.*

**The one-line result: the radius moves the sample by 3.6x and the conclusion
by nothing.** Across the defensible band, 8.3 to 45.0 miles, the treated-unit
count runs 721 to 2,572 ZCTAs and the out-of-sample AUC runs 0.627 to 0.708
against a baseline of 0.689. It never reaches the pre-registered 0.80. The
model beats a constant on Brier by under 1% at every radius, and the constant
is better calibrated at every radius. The one thing that is NOT robust is the
count of "significant" covariates, and §6 argues that change is an artefact of
sample inflation rather than evidence.

---

## 0. A departure from this directory's convention, declared up front

`docs/research/README.md` prescribes seven parts and one file per paper. This
is not a paper; it is a sensitivity analysis whose source evidence is a
commercial trade document. The structure is adapted. Part 7, "what I did NOT
read", survives as §8 and is again the most important section.

---

## 1. What the project uses today, and what justified it

`src/siting_atlas/warehouse/facilities.py`:

```python
CATCHMENT_MILES = {"DS": 15.0, "SDC": 10.0}
```

The docstring above it gives the justification in one sentence:

> *"A delivery station's service area is commonly quoted at 20-30 minutes'
> drive; 15 miles straight-line is the conservative reading of that in
> congested metros."*

and then immediately withdraws the support:

> *"ENGINEERING ESTIMATE. No published source was found for either figure, and
> the '20-30 minutes' is itself an unsourced trade claim."*

`docs/data/PARAMETERS.md` §6.21 records the same, and §5 records the
consequence: the radius does not touch a single cost figure, and it sets the
entire sample the causal stage learns from. `docs/AUDIT_2026_09_14.md` §3.4
ranks it the most consequential unsourced parameter in the project and notes
that the measurement of *how much it matters* exists while the sensitivity
band it demands does not.

**The stated justification does not reproduce the stated value.** Converting a
drive time to a straight-line radius needs a speed and a circuity, and this
project already has both, in `cost/params.py`: `avg_speed_mph = 22.0` and
`circuity = 1.30`. A 30-minute drive is then

    22.0 x 0.5 h / 1.30 = 8.46 straight-line miles

and 20 minutes is 5.64. To get 15 miles out of a 30-minute drive at circuity
1.30 you need an average speed of **39 mph**, which is not a congested metro.
So 15 is not a conservative reading of 20-30 minutes; it is roughly double the
generous reading. This does not make 15 wrong — §2 shows it lands close to a
different, externally stated figure — but the sentence defending it defends a
smaller number.

---

## 2. The external anchor that did not exist before

`docs/data/MWPVL_2025.md` §3.2 quotes the source document's line 383:

> *"[delivery stations are] designed to service a **45-mile radius**."*

That is the only statement in the evidence that describes the general class of
facility this target variable is built from, and it is three times the value
in the code.

The OCR'd tables carry per-building statements too. Measured, not recalled —
`data/interim/mwpvl_facilities.csv`, 1,904 rows:

| what | rows | where |
|---|---|---|
| `"45 minute drive time"` (same-day promise) | 37 | 36 in `01_us_fulfillment_center`, 1 in `08_us_delivery_station` |
| an explicit `N-mile radius` | 7 | 6 in `08_us_delivery_station`, 1 FC |

The seven explicit radii, verbatim:

```
  SNJ1  Woodland Park NJ   (FC)  "within 50 miles radius"
  DYO5  Bridgeport CT      (DS)  "Greater Bridgeport CT area 60 mile radius"
  WWI2  Dubuque IA         (DS)  "deliver 60 miles in all [directions]"
  WMT1  Missoula MT        (DS)  "Rural Wagon Wheel ... within a 50-mile radius"
  DOM1  Omaha NE           (DS)  "within a 90-mile radius"
  DLV1  Columbus NE        (DS)  "Rural Wagon Wheel ... 50- mile radius"
  ----  Fallon NV          (DS)  "Rural Wagon Wheel ... 50- mile radius"
```

An eighth exists and is reported with a caveat: the Jackson TN row in
`08_us_delivery_station_part2` OCRs as the single token `60)=70imile`
(`data/raw/mwpvl/tsv/08_us_delivery_station_part2/img-092__000000.tsv:36`),
i.e. "60-70 mile", **at Tesseract confidence 5 out of 100**. It is treated as
corroboration of the 50-90 cluster and not as a measurement.

Three things follow, and the third is the one that matters.

1. **The radius is no longer a pure guess.** There is a stated design figure
   (45) and seven stated operating figures (50 to 90).
2. **Every stated figure is LARGER than 15.** If the source is taken at face
   value the code is not conservative; it is three to six times too small.
3. **The spread between the statements is itself the evidence about the band.**
   The source does not give one radius, it gives a family, and four of the
   seven explicit ones are "Rural Wagon Wheel" or small-metro buildings, which
   is a different operating model from a dense-metro station. A rural station
   serving 50 miles of farmland and an urban station serving 15 miles of
   Brooklyn are not the same object measured twice.

---

## 3. The endpoints, and why they are not round numbers

Each point on the sweep is anchored, and the conversions all use this
project's own parameters rather than a second set of guesses. Straight-line
miles = `speed x hours / circuity`.

| mi | anchor | arithmetic |
|---|---|---|
| **8.3** | MWPVL "45 minute drive time" at this project's CONGESTED profile (`cost/params.py:295`: 16 mph, circuity 1.45) | 16 x 0.75 / 1.45 = 8.28 |
| 12.7 | The same statement at the cost BASELINE (22.0 mph, 1.30) | 22 x 0.75 / 1.30 = 12.69 |
| 15.0 | The value in the code | — |
| 19.6 | The same statement at the fast, straight end of `montecarlo.COST_RANGES` (30 mph, circuity 1.15) | 30 x 0.75 / 1.15 = 19.57 |
| 25.0 | Holmes (2011)'s 25-mile consumer choice radius; Houde, Newberry and Seim (2023)'s 25-mile FC-to-SC proximity rule. The only two published radii the project cites — neither measures last-mile delivery | — |
| **45.0** | MWPVL line 383, "designed to service a 45-mile radius" | — |
| *60.0* | *OVER-RUN PROBE, outside the band.* The per-building claims at 50-90 describe rural and small-metro buildings, not the nine dense CBSAs this panel is cut to | — |

**Why 8.3 and not 5.** The lower endpoint is a converted external statement,
not the smallest number anyone could defend. 5 miles is in
`PARAMETERS.md` §5 as a measurement, and nothing in the evidence argues for
it: no MWPVL row states a radius below 45, and the shortest drive-time claim
in the document converts to 8.3 at the least favourable speed and circuity
this project allows itself. Going below 8.3 would be picking a number to widen
the band.

**Why 45 and not 90.** 45 is the source's own statement about delivery
stations as a class. 90 is one building in Omaha. Using the largest number in
the document as the upper endpoint would make the band a statement about rural
Nebraska, and the panel contains no rural Nebraska.

---

## 4. Verifying the re-implementation before trusting it

`facilities.py` reads its radius from a module constant and is being rewired
by another workstream, so `catchment_band.py` re-implements the catchment
rule locally. That re-implementation is checked twice before any other point
on the sweep is reported, and it refuses to continue on a mismatch.

**Check 1 — against the delivered panel, cell by cell.** At 15.0 miles, over
all 1,081,312 (ZCTA, quarter) cells of `data/processed/panel.parquet`:

```
  panel.parquet enabled cells      27,914
  recomputed    enabled cells      27,914
  mismatched cells                      0
```

**Check 2 — against the six radii already written down** in `PARAMETERS.md`
§5 and the `CATCHMENT_MILES` docstring. Distinct ZCTAs ever enabled:

| radius | recorded | re-measured | agrees |
|---|---|---|---|
| 5 | 383 | 383 | yes |
| 10 | 882 | 882 | yes |
| 15 | 1,257 | 1,257 | yes |
| 20 | 1,593 | 1,593 | yes |
| 25 | 1,819 | 1,819 | yes |
| 30 | 2,006 | 2,006 | yes |

Six of six, exactly. The downstream fit is checked too: at 15 miles the
pipeline in `catchment_band._fit` reproduces `experiments/hazard-model/artefacts/hazard_report.json`
(run `20260914-002509-2374`) to the digit — risk set 1,756 units / 40,358 rows
/ 812 events, AUC 0.6894, Brier 0.019522, and all five coefficients.

---

## 5. The band

`outputs/metrics/catchment_band.json`. Rows marked `*` are outside the band.

```
     mi   ZCTAs  units  events     AUC     Brier      null  sig
    8.3     721   1977     559  0.7081  0.010743  0.010799    1
   12.7    1093   1833     748  0.6689  0.015633  0.015684    1
   15.0    1257   1756     812  0.6894  0.019522  0.019614    1   <- baseline
   19.6    1568   1610     910  0.6829  0.024315  0.024428    1
   25.0    1819   1444     921  0.6406  0.032288  0.032480    3
   45.0    2572   1076     856  0.6269  0.051275  0.051771    3
 * 60.0    3153    952     805  0.6247  0.061226  0.062151    2
```

`units` and `events` are the risk set after left-truncation. `null` is a
model that predicts one constant, scored on the same test rows. `sig` counts
covariates with p < 0.05, of three.

**Read as a band, in the style `optimize/montecarlo` uses:**

| quantity | 8.3 mi | baseline (15 mi) | 45 mi | max/min over the band |
|---|---|---|---|---|
| ZCTAs ever enabled | 721 | 1,257 | 2,572 | **3.57x** |
| enabled panel cells | 14,121 | 27,914 | 67,216 | **4.76x** |
| facilities attached | 43 | 43 | 43 | 1.00x |
| ZCTAs served by 2+ stations | 57.3% | 72.0% | 80.2% | 1.40x |
| out-of-sample AUC | 0.7081 | 0.6894 | 0.6269 | 1.13x |
| Brier skill vs the constant | 0.0052 | 0.0047 | 0.0095 | 2.98x |

**The last two rows do not run the way the first four do, and the table used
to hide that.** `catchment_band.json`'s `band` block stores a `low` and a
`high` that are the **minimum and maximum over the sweep**, not the values at
the endpoints. For ZCTAs, cells, facilities and coverage the two coincide,
because those rise monotonically with the radius. For AUC and Brier skill they
do not: AUC is highest at the **narrow** end (0.7081 at 8.3 mi) and lowest at
the wide one (0.6269 at 45 mi), and Brier skill's minimum, 0.0032, sits at
**12.7 mi**, not at either endpoint. Until 2026-09-16 this table printed the
artefact's `low` under the 8.3-mile column and its `high` under the 45-mile
column, which inverted the AUC row against the sweep printed fifteen lines
above it and against §6.1's attenuation argument. The **range** — AUC 0.627 to
0.708, Brier skill 0.0032 to 0.0095, and the ratios in the last column — is
unchanged; only the assignment of each end to a radius was wrong.

**This is not a confidence interval.** There is one true catchment radius and
we do not know it. The range is a sensitivity range over an assumption, in
exactly the sense `optimize/montecarlo`'s docstring states about its own
output: it measures how far the answer moves across the range we can defend
from MWPVL's statements, and it propagates our reading of them, not the
world's.

### 5.1 Two things the sweep found that nobody predicted

**`facilities_attached` is flat.** All 43 delivery stations attach at every
radius from 8.3 to 60 miles, because a facility sits inside a ZCTA and so
attaches at least its own. The radius buys ZCTAs **per facility** — 33.3 at
8.3 miles, 87.6 at 15, 293.1 at 45 — and buys no facilities at all. Anyone
reading "the radius controls sample size" as "the radius controls how many
buildings we observe" is reading it wrong: the 43 decisions are 43 decisions
at every radius, and everything the radius adds is replication.

**The risk set SHRINKS as the radius grows.** Units at risk fall monotonically
from 1,977 at 8.3 miles to 1,076 at 45. A wider catchment left-truncates more
ZCTAs — they were already enabled in the first observed quarter, so
`risk_set._drop_left_truncated` removes them — faster than it adds newly
treated ones. Events peak at 921 around 25 miles and fall to 856 at 45. So
"bigger radius, bigger sample" is false past about 25 miles; past that point
the radius is trading units for density.

---

## 6. Is the conclusion robust? Yes, with one exception that is not evidence

The hazard stage's published conclusion (`academic/proposal/PROPOSAL_V5.md`,
around line 1407) is four claims. Each was re-scored at every radius:

| claim | holds at |
|---|---|
| out-of-time AUC reaches the pre-registered 0.80 | **nowhere** in the band |
| the model beats a constant on Brier | every radius, by 0.3% to 0.9% |
| the constant is BETTER CALIBRATED than the model | every radius |
| `households` is distinguishable from zero | every radius |
| exactly one of three covariates is distinguishable | **8.3 / 12.7 / 15 / 19.6 only** |

The first four are invariant across a 4.76x change in the sample. That is the
finding: a parameter with a large, documented lever on the evidence base has
no lever at all on what the evidence says. The right way to quote the headline
is therefore not "AUC 0.69" but **"AUC 0.63 to 0.71 across every catchment
radius the source supports, against a target of 0.80."**

### 6.1 The exception, and why it is not good news

At 25 and 45 miles all three covariates cross p < 0.05, where at 8.3 to 19.6
only `households` does. Read naively that says a wider catchment finds more
signal. It does not, and the coefficients say so:

```
  radius   households    p        median_hh_income   p        establishments  p
    8.3    6.0e-05    0.0000      -2e-06        0.6192      1.16e-04     0.3230
   12.7    5.3e-05    0.0001      -1e-06        0.7451      7.50e-05     0.6453
   15.0    5.2e-05    0.0001       1e-06        0.7804      1.49e-04     0.2977
   19.6    5.1e-05    0.0041       3e-06        0.1444      2.15e-04     0.0710
   25.0    4.3e-05    0.0004       4e-06        0.0371      3.11e-04     0.0006
   45.0    4.5e-05    0.0000       8e-06        0.0016      1.75e-04     0.0327
 * 60.0    3.2e-05    0.0106       8e-06        0.0006      6.40e-05     0.4054
```

The `households` coefficient falls from 6.0e-05 to 4.5e-05 across the band, a
**25% attenuation toward zero**, and to 3.2e-05 (−47%) at the 60-mile probe.
That is exactly the direction `facilities.py` predicted before any of this was
run:

> *"The error is not symmetric: a radius that is too LARGE labels untreated
> ZIPs as treated, which attenuates every hazard coefficient toward zero."*

The prediction is now measured rather than asserted. The p-values fall anyway
because the row count is rising and the standard errors are clustered on only
nine CBSAs — a count `hazard.py` itself warns is below the ~30 needed for the
robust covariance to behave. At 45 miles 80.2% of enabled ZCTAs are inside two
or more catchments, so the added rows are near-duplicates of rows already
there. More stars from more correlated copies of the same 43 decisions is a
sample-inflation artefact, and reporting it as newly discovered signal would
be the error this whole exercise exists to avoid.

---

## 7. How far the chain reaches

Followed, not assumed. `CATCHMENT_MILES` is read in exactly one file — the
other two hits are this sweep's own prose:

```
$ grep -rn "CATCHMENT_MILES" src tests scripts --include=*.py \
    | grep -v -e facilities.py -e catchment_band.py
(no output)
```

`enabled` reaches `models/` (risk set, hazard, covariate search, panel source,
diagnostics) and `agent/`, and nothing else:

```
$ grep -rln "enabled" src/siting_atlas/optimize src/siting_atlas/cost \
      src/siting_atlas/models/choice.py
(no output)
```

So the chain is **radius -> `enabled` -> risk set -> hazard fit**, and it
stops there. The cost model, the discrete-choice model and the portfolio
optimiser never see the target column: the $1.128-1.320bn capital headlines
and the 282-330 activation counts are untouched by the radius, at any value in
or out of the band. That is worth stating plainly because "the most
consequential unsourced parameter" is consequential for the *causal* stage
only, and the two stages are frequently quoted in the same breath.

---

## 8. What this does NOT settle

- **It is still a circle.** A real catchment is a drive-time isochrone shaped
  by roads, water and bridges. Every point on this sweep is a disc. The band
  is over the radius of the disc, not over the disc-versus-isochrone choice,
  and that second error is unmeasured.
- **Every coordinate is a ZCTA centroid.** `warehouse/national.py` records
  that 0 of the 43 pilot rows carry a latitude or longitude, so
  `resolve_coordinates` falls back to the centroid of the facility's own ZIP.
  At 8.3 miles a centroid error of two or three miles is a large fraction of
  the radius; at 45 it is noise. The low end of this band is therefore
  measured less precisely than the high end, and by an unknown amount.
- **`SDC` is still untested.** It is held at 10.0 miles throughout because
  every one of the 43 delivered rows is a `DS`. The band says nothing about it.
- **The band is over the PILOT frame only.** `facility_load.FACILITY_FRAMES`
  offers two larger frames (104 and 693 rows) that produce different targets;
  `data/processed/panel.parquet` is the pilot, and so is everything above.
- **MWPVL's 45 miles is a design statement, not a measurement.** The document
  says stations are *designed to service* 45 miles. It does not say they do,
  and it gives no method. Taking it as the upper endpoint treats a vendor's
  prose as evidence, which is better than treating our own prose as evidence
  and worse than a measurement.
- **The 37 "45 minute drive time" rows are mostly SubSameDay FULFILLMENT
  CENTERS** (36 of 37), not plain delivery stations. A same-day promise from a
  sub-same-day FC is a tighter service than a standard delivery station's
  next-day route, so the three drive-time points are, if anything, low. That
  is the correct direction for a lower endpoint, but it is an argument, not a
  measurement.
- **The document disagrees with itself elsewhere**, by a factor of two on
  delivery-station square footage (`MWPVL_2025.md` §3.4). A source that
  contradicts itself on the defining attribute of the facility class should
  not be read as authoritative on its service radius either. It is the best
  commercial source available and it is not a measurement instrument.

---

## 9. Related

- [`../data/PARAMETERS.md`](../data/PARAMETERS.md) §5 and §6.21 — the register
  entry this note supplies the band for.
- [`../data/MWPVL_2025.md`](../data/MWPVL_2025.md) §3.2 — the 45-mile line,
  and §3.4 for the source's internal contradiction.
- [`../AUDIT_2026_09_14.md`](../AUDIT_2026_09_14.md) §3.4 — the finding.
- `src/siting_atlas/optimize/montecarlo.py` — the module docstring this note
  borrows its "what this is not" framing from.

## 10. Reproducing it

```bash
PYTHONPATH=src .venv/bin/python -m siting_atlas.warehouse.catchment_band
```

About 20 seconds: seven target rebuilds over 1.08m panel cells and seven
hazard refits. Deterministic — the split seed is
`common.seeds.seed("evaluation", "train_test_split")` and nothing else is
random. Writes `outputs/metrics/catchment_band.json`.
