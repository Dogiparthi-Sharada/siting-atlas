# Highway access — built, measured, and it does not move the model

*Written 2026-09-14/15. Code `src/siting_atlas/ingest/tiger_roads.py` and the
`tiger_*` helpers beside it. Artefact `data/interim/highway_access.parquet`,
14,767 ZCTAs. Result `outputs/metrics/highway_access.json`. Raw
`data/raw/tiger_roads/` (1.7 GB), manifest lines `tiger_roads` and
`tiger_roads_county`.*

**Status: BUILT, TESTED, NEGATIVE.** The covariate is real, it is measured
correctly, and it has a strong raw association with where Amazon builds — the
chosen ZCTA sits at the **74th percentile of its own metro** on interchange
count. Inside the choice model it is worth almost nothing. Every coefficient
lands in the **interior**, which nine of the project's ten previous covariates
failed to do, and the held-out lift moves by fractions of a percentage point
in either direction with intervals that cover zero everywhere.

The short version: highway access is not absent from the model, it is
**already in it**, wearing the names `households` and `establishments`.

---

## 1. Why it was built, and why `traffic_proximity` was not this

Every industry account of delivery-station siting puts freeway adjacency at or
near the top. The building takes line-haul semis overnight and releases several
hundred vans in a morning wave, and both flows have to reach a freeway without
being routed down residential streets.

The panel already holds `traffic_proximity` and it looks like it should measure
this. It does not. It is EJScreen's **pollution-exposure** variable: the traffic
count on road segments within 500 m of the block, distance-weighted. It is
large wherever a lot of vehicles pass nearby, whether or not anything can get on
or off. Tested as a covariate on 2026-09-14 it returned **+0.07 lift**, i.e.
nothing. Exposure and access are different concepts.

This module measures access.

## 2. The data, and the one thing the cheap file does not contain

| layer | what | size | MTFCC |
|---|---|---|---|
| `TIGER2023/PRIMARYROADS/tl_2023_us_primaryroads.zip` | one national file, freeway and highway centrelines | 37 MB | `S1100` only |
| `TIGER2023/ROADS/tl_2023_<county>_roads.zip` × 901 | all roads, per county — fetched for the **ramps** | 1.6 GB | `S1630` among others |

Both are bulk downloads, no API and no rate limit, and both are in
`data/raw/manifest.jsonl` with a SHA-256. The national file gets an ordinary
manifest line. The 901 county files get **one** line whose hash is the hash of
`data/raw/tiger_roads/roads_sha256.txt`, which carries one SHA-256 per county
file in `sha256sum -c` format — 901 manifest lines would have buried every
other source in the file, and the chain is still checkable end to end:

```
cd data/raw/tiger_roads/roads && sha256sum -c ../roads_sha256.txt
```

**The national file has no ramps.** Measured, not assumed: of its 17,458
features, `MTFCC` takes exactly one value (`S1100`) and exactly one feature has
"Ramp" anywhere in `FULLNAME`. `PRISECROADS` adds `S1200` and no ramps either.
That matters, because the constraint is not "near a freeway", it is **near a
freeway exit** — and a ZCTA can be crossed by eight lanes of interstate for four
miles with no way on or off it. So the county files were fetched too, for the
900 counties of the 235 metros that contain a facility. This is the expensive
half of the build and it is the half that measures the real constraint.

`RTTYP` separates Interstates (`I`, 5,599 features) from US routes, state
highways and named expressways. Both are measured. Alaska is why: the Glenn and
Seward highways are the line-haul routes into Anchorage and TIGER codes neither
as `I`.

## 3. Ramps are not interchanges

Los Angeles County has **4,177** `S1630` features. It does not have 4,177
interchanges. A four-level stack is dozens of features and how many depends on
where TIGER split the linework, which is a cartographic accident and not a fact
about the road. Counting features would measure TIGER's digitising conventions.

So the ramps are **clustered**: every ramp in a county is buffered by 150 m, the
buffers are dissolved, and each connected component is one interchange. LA
County collapses from 4,177 features to **320** components, the right order for
a county with roughly 330 freeway junctions. Nationally, across the 900
counties: **143,226 ramp features → 23,812 interchanges.**

The 150 m radius is a parameter and is reported as one. It has to exceed the
width of the carriageways separating the two halves of a diamond interchange
(50–100 m) or every diamond counts twice, and it has to stay well under the
spacing of genuinely distinct exits (≈800 m–1 km in a dense corridor). 150 m
sits inside both bounds with room either side. Measured sensitivity, same
143,226 ramp features:

| radius | interchanges | vs default |
|---|---|---|
| 100 m | 26,398 | +10.9% |
| **150 m** | **23,812** | — |
| 250 m | 19,869 | −16.6% |

A 67% change in the radius moves the count by about a sixth, in the direction
it should and with no cliff between. Counties are clustered
independently, so an interchange sitting exactly on a county line is counted in
both; that is a real error and a small one, and fixing it would mean dissolving
three-quarters of a million features in one operation.

## 4. What is in the artefact

One row per ZCTA, 14,767 of them — the ZCTAs of the 235 metros that contain a
facility, which is every ZCTA the conditional choice model can ever put in a
choice set. `ramp_coverage` is `True` for 14,764 of them; the three exceptions
are the ZCTAs of one Kentucky county whose ROADS file the Census WAF refused on
every attempt (HTTP 200 with a 247-byte "Request Rejected" page, from two user
agents, while the adjacent county served normally). Those rows carry **NULL**
on the interchange columns, not zero — a zero would read as "this ZCTA has no
exit", which is a measurement, when the truth is "nobody looked".

| column | kind | median | share at zero | n |
|---|---|---|---|---|
| `primary_road_dist_km` | distance | 0.00 km | 50.5% | 14,767 |
| `interstate_dist_km` | distance | 1.68 km | 38.0% | 14,653 |
| `interchange_dist_km` | distance | 0.00 km | 53.1% | 14,764 |
| `primary_road_miles` | **extensive** | 0.31 mi | 49.4% | 14,767 |
| `interstate_miles` | **extensive** | 0.00 mi | 62.2% | 14,767 |
| `interchanges` | **extensive** | 1.00 | 46.3% | 14,764 |

The 114 ZCTAs missing `interstate_dist_km` are in Puerto Rico and Alaska,
where TIGER codes no `S1100` feature as `RTTYP='I'`. Puerto Rico's PR-22 and
PR-52 *are* Interstate-funded highways and TIGER calls them `M`; that is a
labelling fact about the source, not a fact about the island, so the column is
NULL there rather than a large number. It costs those metros their place in
the fitted frame and they are counted in the coverage block of the artefact.

Three decisions in that table are worth defending.

**Polygon, not centroid.** Every distance is from the ZCTA *polygon* to the
feature — the shortest distance from any point of the zone. The centroid of a
large rural ZCTA can be miles from anywhere a developer would look, and that is
exactly the case where a highway covariate should have something to say.

**Which is also why the distances are half useless.** Polygon distance is
exactly zero whenever the feature crosses the zone at all, and it does for 38%
of ZCTAs on interstates and 53% on interchanges. A column that is constant over
half its support has thrown away half of what it could have said. That is the
argument for the mileage and count columns existing, and it is why the headline
specification is `interchanges` and not a distance.

**Extensive where possible.** `choice.py`'s docstring explains that the
`ln(beta'a)` functional form exists so the model is invariant to how the Census
drew the zone boundaries, and that invariance holds only for variables that
*add* under a merger of zones. Counts and lengths add. A distance does not, so
`highway_access` and its siblings are a workaround and are labelled one
wherever they appear.

**Projection.** TIGER ships in EPSG:4269, which is degrees, and a distance in
degrees is not a distance. `osm_landuse.py` uses EPSG:5070 (Albers CONUS);
that is right inside the CONUS and wrong outside it, and this project has four
metros outside it — Anchorage, Honolulu, San Juan, Aguadilla — with 152 panel
ZCTAs between them. Each region is measured in the projection its own mapping
agency uses (5070 / 3338 / 26963 / 32161). The nearest-feature *index* is
queried on geometry simplified to 25 m and the distance is then taken between
the full-resolution pair, so the tolerance can only pick the wrong feature, not
report a wrong number: worst case 13 m, p99 2.4 m, on distances in kilometres.

### Validated against known geography

| ZIP | | interstate dist | interstate mi | interchanges | ramp dist |
|---|---|---|---|---|---|
| 10001 | Manhattan midtown | 0.93 km | 0.00 | 0 | 0.11 km |
| 90058 | Vernon CA, industrial | 0.00 km | 0.64 | 1 | 0.00 km |
| 60106 | Bensenville IL, air cargo | 0.05 km | 0.00 | 0 | 0.47 km |
| 07105 | Newark NJ, port | 0.00 km | 14.70 | 2 | 0.00 km |
| 90210 | Beverly Hills | 2.66 km | 0.00 | 0 | 1.54 km |
| 11211 | Williamsburg, Brooklyn | 0.00 km | 2.60 | 1 | 0.00 km |

Midtown has no interstate inside it and the Lincoln Tunnel helix 110 m away;
Beverly Hills is 2.7 km from the 405 and the 10; the Newark port ZIP has 14.7
miles of the Turnpike and I-78 running through it. These are right.

## 5. The raw association is strong

Within each metro, rank every ZCTA on a column and take the percentile of the
one Amazon actually chose. 0.5 means no signal. 613 chosen ZCTAs:

| column | percentile of the chosen ZCTA |
|---|---|
| `primary_road_miles` | **0.745** |
| `interchanges` | **0.741** |
| `interstate_miles` | 0.698 |
| `interchange_dist_km` | 0.339 *(lower is better)* |
| `interstate_dist_km` | 0.318 *(lower is better)* |

Median chosen ZCTA: 3 interchanges and 5.8 interstate miles. Median unchosen
ZCTA in the same metros: 1 interchange and 0.0 interstate miles.

This is a real and large univariate association, and on its own it would be a
finding. It is not the question the model asks.

## 6. What the model asks, and the answer

The question is whether highway access adds anything **the four baseline
columns do not already carry**. It does not, and the reason is visible before
the model runs — Spearman correlation across the 14,767 in-scope ZCTAs:

| | households | land_area_sqmi | establishments |
|---|---|---|---|
| `interchanges` | 0.530 | 0.208 | 0.513 |
| `primary_road_miles` | 0.492 | 0.150 | 0.488 |
| `interstate_miles` | 0.348 | 0.140 | 0.347 |
| `highway_access` | 0.546 | 0.075 | 0.533 |

Note what the confound is *not*. The obvious worry is area — a big ZCTA has
more of everything — and area is the **weakest** of the three (0.21). The
covariate is collinear with *urbanisation*: the ZIPs with interchanges in them
are the ZIPs with people and businesses in them, and the baseline already
counts both.

### 6.1 The experiment

`src/siting_atlas/ingest/tiger_lift.py`, which is
`models/covariate_search.py`'s harness narrowed to one source and copied
rather than improved on, so the number is comparable to the nine covariates
already tested. **482 decisions, 86,665 alternatives, 50 paired re-splits**
at the project's standard 60/40, every arm a column subset of one frame so the
choice sets are identical, and the baseline refitted inside every split so
every difference below is a *within-split* difference.

Distinct decisions by choice-set size: **64** small (≤25), **161** mid
(26–100), **257** large (>100).

Eight arms: the baseline four, then the baseline plus each of six
specifications one at a time, then one combination. All eight were declared
before the run and all eight are below.

### 6.2 Every coefficient is interior — which is itself news

| arm | β on the added column (median of 50) | p10–p90 | at the boundary on |
|---|---|---|---|
| `+ interchanges` | **0.508** | 0.302 – 0.757 | 0% of splits |
| `+ primary_road_miles` | **0.370** | 0.227 – 0.542 | 0% |
| `+ interstate_access` | **0.191** | 0.118 – 0.311 | 0% |
| `+ interstate_miles` | **0.105** | 0.057 – 0.179 | 0% |
| `+ highway_access` | 0.070 | 1.7e-13 – 0.154 | 12% |
| `+ interchange_decay` | 0.037 | 2.7e-15 – 0.096 | 30% |
| `+ interchanges + highway_access` | 0.512 / **3.1e-14** | — | 0% / **64%** |

β is in mean-scaled units, so `interchanges` = 0.508 reads as: *at its mean, a
ZCTA's interchange count contributes half as much attraction as its household
count does at its mean.* That is not a small number.

Four of the project's previous covariates produced output **identical to the
baseline to fifteen decimals** — the optimiser drove them to β → 0 and they
contributed literally nothing. These do not. The largest single-alternative
probability difference from the baseline on a split is **0.36** for
`interchanges`, not 1e-15. The model is genuinely using the column.

The last row is the most informative one in the table. Put `interchanges` and
`highway_access` in together and the distance term is driven to the boundary on
**64% of splits** while the count stays put. The count subsumes the distance:
once you know how many exits are in the ZIP, how far the nearest one is adds
nothing. That is also the answer to "should this have been a distance?" — no.

### 6.3 And the lift does not move

Paired change in held-out hit rate against the baseline, in percentage points,
mean of 50 splits ± 2 standard errors. `*` marks an interval excluding zero.

| arm | top-5 small | top-5 mid | **top-5 large** | top-10 small | top-10 mid | **top-10 large** |
|---|---|---|---|---|---|---|
| `+ interchanges` | +3.98 ±1.22\* | +2.14 ±0.61\* | **+0.56 ±0.32\*** | −1.29 ±0.63\* | +0.69 ±0.70 | **+0.12 ±0.16** |
| `+ interstate_miles` | +2.40 ±1.28\* | +0.98 ±0.55\* | +0.01 ±0.21 | +0.66 ±0.44\* | +0.11 ±0.72 | **−0.13 ±0.12\*** |
| `+ primary_road_miles` | +5.20 ±1.31\* | +5.35 ±0.81\* | −0.04 ±0.22 | +1.72 ±0.60\* | +1.29 ±0.77\* | −0.11 ±0.30 |
| `+ highway_access` | +0.68 ±0.45\* | +0.22 ±0.16\* | +0.05 ±0.15 | +0.02 ±0.23 | +0.42 ±0.32\* | +0.00 ±0.00 |
| `+ interstate_access` | +3.92 ±0.92\* | −0.47 ±0.22\* | +0.03 ±0.19 | +0.16 ±0.22 | −0.13 ±0.66 | **−0.29 ±0.13\*** |
| `+ interchange_decay` | +0.38 ±0.32\* | +0.12 ±0.12\* | +0.08 ±0.11 | +0.09 ±0.17 | +0.18 ±0.20 | +0.00 ±0.00 |
| `+ interchanges + highway_access` | +4.07 ±1.21\* | +2.08 ±0.60\* | +0.54 ±0.32\* | −1.37 ±0.64\* | +0.65 ±0.71 | +0.12 ±0.16 |

At top-1, `interchanges` is **−0.21 ±0.11** in large metros: significantly
*worse*.

Reading it honestly, three things:

**The sign flips with `k`.** `interchanges` in large metros is −0.21 pp at
top-1, +0.56 pp at top-5 and +0.12 pp at top-10. A covariate carrying
information the baseline lacks does not help at one threshold, hurt at
another and vanish at a third. This is re-shuffling the ranking, not
sharpening it.

**The positive numbers are in the strata that cannot show much.** The big
figures — +5.35 pp for `primary_road_miles` in mid metros — are where a
uniform guess already scores 22.6% at top-10 and lift is capped near 1.5x in
small metros whatever the model does. In the stratum this covariate was built
for, 300-candidate metros, the effects are between −0.3 and +0.6 pp.

**The standard errors are understatements and are left as such.** 50 re-splits
of one 482-decision frame are not 50 independent draws, so the true intervals
are wider than these. Since almost every interval already covers zero,
widening them cannot change a conclusion — but it does mean the handful of
starred cells should not be read as findings.

### 6.4 The criterion that uses every decision says it plainly

Top-k throws away everything except whether the chosen ZCTA crossed a
threshold. The mean probability the model puts on the ZCTA Amazon actually
chose uses all of it:

| arm | mean P(chosen), held out |
|---|---|
| **baseline** | **0.07478** |
| `+ interchange_decay` | 0.07357 |
| `+ highway_access` | 0.07318 |
| `+ interstate_access` | 0.07222 |
| `+ interchanges` | 0.07205 |
| `+ interchanges + highway_access` | 0.07180 |
| `+ interstate_miles` | 0.07147 |
| `+ primary_road_miles` | 0.07141 |

**Every specification is worse than the baseline, without exception**, by 1.6%
to 4.5% relative. That is what a fifth parameter fitted on 289 training
decisions does when it carries no information the other four lack: it buys
in-sample fit and pays for it out of sample.

### 6.5 Verdict

Highway access **does not improve the model**, and the project's tenth
covariate fails like the first nine. But it fails differently, and the
difference is worth recording rather than filing under "another null":

- it is **not** at the boundary — the model uses it, β is a third to a half of
  the numeraire, and the scores move by up to 0.36;
- the raw association is large and in the expected direction (74th within-metro
  percentile);
- and it still does not predict, because `interchanges` correlates 0.53 with
  households and 0.51 with establishments, and the baseline already counts
  both.

The right reading is that **highway access was never missing from the model.**
Amazon does build next to freeway exits — the raw data says so loudly — but
the ZIPs with freeway exits in them are the ZIPs with people and businesses in
them, and a model that already knows how many households and how many
establishments a ZIP has already knows, to a first approximation, whether it
has an interchange. The covariate is a different *measurement* of the same
underlying thing, not a different thing.

One honest caveat against my own conclusion. Interchange **count** is
"how much freeway infrastructure is in this ZIP", which is close to a density
measure and therefore close to what the baseline carries. It is not the same as
"can a semi get from the ramp to this parcel without crossing residential
streets", which is a **routing** question about a specific site and cannot be
answered at ZCTA grain by any of these columns. What is refuted here is that
ZCTA-level highway geometry adds information. Whether parcel-level ramp access
would is untested and untestable on this panel.


## 7. Reproducing it

```
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.tiger_roads
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.tiger_lift
```

The first is ~12 minutes of CPU (the nearest-feature passes dominate) plus a
one-off 1.6 GB download; the interchange layer is cached to
`data/interim/tiger_interchanges.parquet` and `--no-cache --cluster-m N`
rebuilds it at another radius. The second is 50 paired re-splits × 8 arms.

| module | job |
|---|---|
| `tiger_fetch.py` | downloads, manifest, the SHA-256 sidecar, the Connecticut substitution |
| `tiger_geom.py` | projections, polygon distance, length-inside, count-inside |
| `tiger_ramps.py` | ramps → interchanges by buffered dissolve |
| `tiger_scope.py` | coverage marking, the summary statistics |
| `tiger_roads.py` | the L1 build, writes `highway_access.parquet` |
| `tiger_frame.py` | the panel with the highway columns on it |
| `tiger_lift.py` | the experiment |
| `tiger_print.py` | its console table |

## 8. Three things found on the way that were not the point

**Connecticut has no counties.** It abolished them as statistical geography in
2022 and the Census replaced them with nine planning regions. TIGER 2023
publishes ROADS under the new codes and none of the old ones, so a run asking
for `09001`–`09015` gets eight 404s and **silently loses Hartford, Bridgeport
and New Haven** — three metros with delivery stations in them. The panel still
carries the old codes. `tiger_fetch.STATE_SUBSTITUTIONS` requests all nine
regions whenever any Connecticut county is asked for.

**`www2.census.gov` answers a burst with HTTP 200 and an error page.** A
247-byte "Request Rejected" body, which `requests` reports as a successful
download because it *is* one — of an error page. One slipped through the
900-county run and GDAL later reported it as "does not exist in the file
system". `MIN_ZIP_BYTES` now rejects anything under 20 KB (the smallest real
county file here is 44 KB).

**`choice.fit` can return a NaN fit and nothing notices.** It keeps the best of
five starts with `best is None or r.fun < best.fun`, so the first start is
accepted unconditionally — including when it returned NaN, after which every
`r.fun < nan` is False and the NaN is never displaced. With `beta = exp(theta)`
an unlucky BFGS excursion overflows theta, `beta'a` becomes `inf`, `inf/inf` is
NaN. The first run of this experiment hit it and the only trace was a `nan` in a
printed mean. `models/` is owned elsewhere so the fix is not applied here;
`tiger_lift` instead checks every split for finite scores, drops a bad split
from that arm only, and prints the count. **Anything else fitting this model
should check.**
