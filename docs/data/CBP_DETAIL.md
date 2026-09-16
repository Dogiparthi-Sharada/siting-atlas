# CBP ZIP x industry — the warehousing covariate, and why its lag guard does not hold

*Written 2026-09-14. Source code `src/siting_atlas/ingest/cbp_detail.py`.
Artefact `data/interim/cbp_detail.parquet`, 210,745 rows across six vintages.
Consumed by `src/siting_atlas/models/choice.py` as `CBP_ATTRACTIONS`. Every
number below was measured from the files on disk today; the commands are in
§7.*

This is the single covariate that made the conditional choice model do
anything at all, and it is also the covariate with the most serious open
defect in the project. Both halves are below, in that order, because reversing
them would be marketing.

---

## 1. What it is

County Business Patterns, ZIP-code-by-industry detail file. The Census Bureau
publishes, for every ZIP and every NAICS code, how many establishments operate
there. We read four codes and keep them as columns:

```
  CBP code   column                        what it counts
  --------   ---------------------------   ------------------------------
  493///     warehousing_establishments    warehousing and storage
  484///     trucking_establishments       truck transportation
  492///     courier_establishments        couriers and messengers
  ------     all_establishments            every industry, the ZIP total
```

Six vintages, 2017 to 2022, 35,002-35,279 ZIPs each.

This is **not** the same source as [`cbp_zip`](cbp_zip.md) in the registry.
That one is `zbp{yy}totals.zip`, one row per ZIP, no industry breakdown, and it
feeds the panel's `establishments` column. This one is `zbp{yy}detail.zip`, one
row per ZIP *and* industry, and it feeds only the choice model.

## 2. Why it exists

The choice model fitted on `households`, `land_area_sqmi` and `establishments`
does not work, and it cannot, because all three are proxies for "how much
stuff is here". A model of that shape is a population map with extra steps.

The binding physical constraint on a delivery station is industrially zoned
land with a suitable building on it. You cannot site one in a residential ZIP
however many households it has. Warehousing establishment counts are the
closest free proxy for that constraint.

**Measured, on the held-out 38 decisions, all four covariates fitted jointly
and the split held fixed at seed 20260914:**

```
  specification                                 rho-sq   top-1   top-5   top-10
  ------------------------------------------   ------   -----   -----   ------
  3 covariates, 100 decisions, 40 held out      0.0920    2/40    7/40   12/40
  4 covariates,  94 decisions, 38 held out      0.1969    7/38   16/38   19/38

  the same comparison on the SAME 94 decisions and the SAME test split:
  3 covariates, warehousing column removed      0.0954    0/38    8/38    9/38
  4 covariates                                  0.1969    7/38   16/38   19/38
```

The headline usually quoted is "30% to 50% at top-10", which is the first pair.
**It is confounded**: the two rows are not the same decisions, because adding
the covariate drops six facilities (§4). The second pair is the clean
comparison — same facilities, same split, one column added — and it is
**23.7% to 50.0%**, a larger effect than the confounded one. Quote the second.

**And one thing this does not buy.** `outputs/metrics/choice_report.json`
records that ranking ZCTAs by the raw `warehousing_establishments` count, with
nothing fitted and no parameters at all, gets **20 of 38** at top-10 — one
better than the fitted four-parameter model's 19. The covariate works. The
estimation on top of it does not.

## 3. The hierarchy trap

CBP pads NAICS to six characters with `/` and `-`, and the file is
**hierarchical**: every establishment is counted at *every* level of its code.

```
  ------   all industries        \
  48----   transportation         |  the SAME establishment appears
  493///   warehousing/storage    |  at all six of these levels
  4931//   warehousing            |
  49311/   general warehousing    |
  493110   general warehousing   /
```

So `493///` is the warehousing total for the ZIP, and the sub-codes must not
be added to it. Summing `493///`, `4931//`, `49311/` and `493110` multiplies
the count by roughly four and produces a covariate that looks fine, correlates
with the right things, and is wrong by a constant factor that varies by ZIP
with the industry mix. The `WANTED` dictionary in `cbp_detail.py` selects
exact padded codes for this reason, and a maintainer who adds a code should
check it is not a descendant of one already in the set.

**A zero is a real zero here.** A ZIP with no `493///` row has no warehousing
establishments, which is a measurement, not a gap. Treating it as NULL would
drop exactly the residential ZIPs the covariate exists to distinguish from
industrial ones, so `extract()` fills with 0 and the module says so.

## 4. The 2016 vintage break

The 2016 file is on disk and is **deliberately excluded**. Measured today by
re-running `extract()` over both files:

```
  vintage   rows in the file   ZIPs   ZIPs with any 493///   median 493 where > 0
  -------   ----------------   ----   --------------------   --------------------
    2016           8,418,283   38,722                 6,165                      1
    2017           2,870,579   35,279                 1,794                      4
```

Establishment counts in the real economy do not fall by two thirds in one
year, and a median that goes from 1 to 4 while the count of reporting ZIPs
falls by 71% is a change in what Census publishes, not a change in what
exists. **The cause was not established and is not guessed at here.** The 2016
file has 2.9 times the rows of 2017, which suggests a change in disclosure or
in the depth of the code hierarchy published, but that is a hypothesis and it
was not tested.

Splicing the two would put a large artificial step in the covariate exactly
where the panel begins. So 2016 is dropped, `load()` logs a warning naming the
file it skipped, and the six facilities that would need it are reported rather
than scored on an incomparable vintage.

## 5. The lag guard is nominal, and this is the defect

This is the part that undercuts §2, and it is stated at the top of the section
rather than at the bottom.

### 5.1 What the guard is for

An Amazon delivery station **is** a warehousing establishment. If it opened
before the CBP vintage we read, it is counted in its own ZIP's `493///` total,
and using that total to predict where Amazon built is circular: the covariate
contains the outcome. `vintage_for()` therefore selects, per facility, the
latest vintage **strictly** earlier than the facility's opening year. Strictly
rather than "at or before", because CBP's reference period is the week of 12
March and a January opening would already be in that year's file.

That is the right design. It rests on `open_year` being an opening year.

### 5.2 `open_year` is not an opening year

Measured today against `data/external/facility_panel/national_facilities.csv`
and `data/collection/results/NATIONAL_CLASSIFIED.csv`:

> **`open_year` and `open_quarter` equal the year and quarter of the OSHA
> inspection date for 104 of 104 national rows. Not most of them. All of
> them.**

`open_year` is therefore **the earliest date OSHA is known to have found the
building operating**. It is an upper bound on the opening, and nothing else. A
station that opened in 2019 and was first inspected in 2024 is recorded as
opening in 2024.

### 5.3 What that does to the guard

The guard lags off the bound, so the margin against the *true* opening is
zero. Concretely, for a station that really opened in 2019 and carries
`open_year = 2024`:

```
  vintage_for(2024) selects CBP 2022
  the station has been operating since 2019
  CBP 2022 counts it
  the covariate contains the outcome, which is exactly what the guard
    exists to prevent, and the guard reports success
```

The guard is not wrong as code. It is correct against the wrong quantity, and
it cannot detect the problem because nothing in the pipeline knows the true
opening date — that is the gap the satellite attempt
([`SATELLITE.md`](SATELLITE.md)) tried and failed to close.

### 5.4 How bad is it, honestly

Unknown, and that is the finding. We cannot bound it, because bounding it
requires the lower bound on the opening date we do not have. Three things can
be said:

- **The direction of the bias is toward the model looking better than it is.**
  Any contamination inflates `warehousing_establishments` in precisely the
  ZCTAs that were chosen, which is the covariate the model leans on hardest.
- **It is not total.** Six facilities were dropped outright for having no
  usable earlier vintage (`open_year` 2013, 2015, 2016 and three at 2017), and
  the newest vintage is 2022, so any station whose OSHA bound is 2023 or later
  is scored on 2022 regardless. For the **57 of 104** rows with
  `open_year >= 2023` the guard is doing nothing beyond capping at the last
  available file.
- **The 2018-2022 rows are where the risk concentrates.** There the selected
  vintage moves with `open_year`, so an OSHA bound that lags the true opening
  by two or three years puts the facility inside its own covariate.

### 5.5 What would fix it

In order of cost:

1. **Rename the column.** `open_year` should be `operating_by_year`
   everywhere. Half the danger here is a field whose name asserts something
   the data does not contain. This is an afternoon and it prevents the next
   reader making the same mistake.
2. **Widen the lag deliberately.** Score every facility on a fixed vintage
   well before the panel — 2017 for all of them — and accept a staler
   covariate in exchange for a guard with real margin. This is testable
   immediately: re-fit on the 2017 vintage for every facility and see how much
   of the 50% survives. If most of it does, the contamination was not doing
   the work; if it collapses, it was.
3. **Get a true opening date.** The only real fix, and the one that has
   already failed once.

Until at least (2) is run, **the warehousing result should be presented with
this caveat attached**, not as a clean out-of-sample gain.

## 6. Provenance, and a second gap

The seven `zbp??detail.zip` files are in `data/raw/cbp_zip_detail/`. They are
**not** in `src/siting_atlas/ingest/sources.py`, not in
`data/raw/manifest.jsonl`, and not fetched by `ingest.acquire`. They were
downloaded by hand.

That breaks the rule in [`README.md`](README.md): "Every download is written
once into `data/raw/<source>/<hash>.<ext>` and appended to
`data/raw/manifest.jsonl` with its SHA-256, byte count, Content-Type and the
run that fetched it." For this source there is no hash, no recorded URL and no
recorded fetch time. A reviewer cannot verify that the file on our disk is the
file Census publishes.

The URL pattern is the same family as the registered `cbp_zip` source:

```
  https://www2.census.gov/programs-surveys/cbp/datasets/{year}/zbp{yy}detail.zip
```

`osm_landuse` has the same gap, for the same reason. Registering both is a
small change to `ingest/sources.py` and it is not this document's to make; it
is recorded here so the omission is visible.

## 7. How to reproduce

```
  PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.cbp_detail
```

Prints one line per vintage with the ZIP count, the count with any warehousing
establishment, and the median where present. The 2016 exclusion is logged as a
warning naming the file.

The `open_year` finding in §5.2 is one join:

```python
import pandas as pd
nf = pd.read_csv("data/external/facility_panel/national_facilities.csv")
nc = pd.read_csv("data/collection/results/NATIONAL_CLASSIFIED.csv")
nf["addr"] = nf.site_address.str.upper().str.strip()
nc["addr"] = nc.address.str.upper().str.strip()
m = nf.merge(nc[["addr", "operating_by"]], on="addr")
ob = pd.to_datetime(m.operating_by)
print(((m.open_year == ob.dt.year) & (m.open_quarter == ob.dt.quarter)).sum(),
      "of", len(m))                                          # 104 of 104
```

The §2 comparison is in `src/siting_atlas/models/choice_runner.py`; running it
with `data/interim/cbp_detail.parquet` absent gives the three-covariate row,
and the module logs a warning saying so.

## 8. Related

- [`cbp_zip.md`](cbp_zip.md) — the registered ZIP-totals source, a different file.
- [`SATELLITE.md`](SATELLITE.md) — the failed attempt to get a real opening date.
- [`OSM_LANDUSE.md`](OSM_LANDUSE.md) — the direct measurement this proxies for, built and blocked.
- [`FACILITY_PANEL_PROVENANCE.md`](FACILITY_PANEL_PROVENANCE.md) — where `open_year` comes from.
