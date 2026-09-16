# Data Acquisition Guide

**What to download, where to put it, and how to check it landed correctly.**

Four sources download automatically from this machine. Six do not. This guide
covers the six, in priority order — highest value for least effort first.

> **Link confidence.** I probed every URL below from the build machine.
> ✅ means I confirmed it responds. 🔒 means the network here blocks that host
> entirely, so I could not verify the deep link and you should navigate from
> the landing page rather than trust a path that may have moved.

---

## Where everything goes

One rule: **each source gets its own folder under `data/external/`, named
exactly as the registry key.** Keep the publisher's original filename.

```
  siting-atlas/
    data/
      external/
        zillow_zori/      Zip_zori_uc_sfrcondomfr_sm_month.csv
        zillow_zhvi/      Zip_zhvi_uc_sfrcondo_tier_...csv
        bls_oes/          oesm23ma.zip
        eia_prices/       <whatever the export is called>
        ejscreen/         EJScreen_..._Tract_....csv
        facility_panel/   facilities.csv          <- see section 6
```

The folder name matters; the filename does not. The loader matches on folder.

**Do not unzip anything.** The pipeline reads archives directly, and keeping
them zipped preserves the checksum that goes in the provenance manifest.

---

## Priority order

| # | Source | Effort | What it unlocks | Without it |
|---|---|---|---|---|
| 1 | **Census API key** | **5 min** | All demographic covariates, nationally | The model runs on ~4 features instead of ~20 |
| 2 | **Facility panel** | hours–days | **The target variable** | No backtest is possible at all |
| 3 | Zillow ZORI + ZHVI | 5 min | Land-cost proxy, monthly currency signal | Cost model loses its largest bucket |
| 4 | EJScreen | 10 min | The equity overlay | No demographic burden map |
| 5 | BLS OES | 10 min | Metro wage variation | Wages fall back to a national average |
| 6 | EIA prices | 10 min | Fuel and energy bucket | Small; a constant is acceptable |

**If you only do two, do 1 and 2.** Number 1 is five minutes and transforms
the feature set. Number 2 is the target variable — without it there is
nothing to predict.

---

## 1. Census API key — do this first ✅

Unlocks the American Community Survey: income, population, age, household
size, tenure, vehicle availability, for all 33,000 ZCTAs. This is the single
highest-value item on the list and it takes five minutes.

**Steps**

1. Go to **https://api.census.gov/data/key_signup.html** *(confirmed reachable)*
2. Fill in: organisation `California State University, East Bay`, your email,
   and tick the agreement.
3. Submit. The key arrives by email, usually within a minute. It is a
   40-character hexadecimal string.
4. Click the activation link in that email — **the key does not work until
   you do**.

**Hand it to me** by pasting the key in chat, or put it in a file I can read:

```bash
echo 'CENSUS_API_KEY=your_40_char_key_here' > siting-atlas/.env
```

`.env` is already gitignored, so it will not be committed.

**How I verify it:** I run `python -m siting_atlas.ingest.probe` and the two
ACS rows flip from `needs_key` to `open`.

> **Why the key is needed at all:** the endpoint returns an HTML page titled
> "Missing Key" with an HTTP **200** status when the key is absent. That is
> why the fetcher asserts on Content-Type — a naive client would cache the
> error page as if it were data.

---

## 2. Facility panel — the target variable 🔨

This is the hardest item and the most important. There is no public API. It
is what we are predicting, so its quality bounds every accuracy number we
report.

### What I need

A single CSV, `data/external/facility_panel/facilities.csv`, with these
columns. Column names must match exactly; order does not matter.

| Column | Type | Required | Example | Notes |
|---|---|---|---|---|
| `facility_id` | text | yes | `AMZ-DAX5` | Any stable unique id |
| `operator` | text | yes | `Amazon` | `Amazon`, `Walmart`, `Costco`, `Target` |
| `facility_type` | text | yes | `DS` | `FC`, `SC`, `DS`, `SDC`, `AMXL` |
| `city` | text | yes | `Hayward` | |
| `state` | text | yes | `CA` | Two-letter |
| `zip` | text | yes | `94545` | 5 digits, **keep leading zeros** |
| `latitude` | number | no | `37.6219` | Blank is fine — I geocode from ZIP |
| `longitude` | number | no | `-122.0808` | |
| `open_year` | integer | yes | `2024` | |
| `open_quarter` | integer | no | `3` | 1–4. Blank means "year known only" |
| `square_feet` | integer | no | `140000` | |
| `status` | text | no | `open` | `open`, `announced`, `closed` |
| `source_url` | text | **yes** | `https://...` | Where you found it |
| `source_type` | text | yes | `press_release` | `press_release`, `news`, `permit`, `inventory`, `company_site` |
| `confidence` | text | no | `high` | `high` if two independent sources |

A template with the header row and three worked examples is at
`data/external/facility_panel/TEMPLATE.csv`.

### Where to find the records

**Option A — company announcements (most reliable, slowest).**
Operators publish facility openings in newsroom posts and regional press
releases. Search `"<operator> opens delivery station <state> 2024"`. These
give an exact date and are the highest-confidence source.

**Option B — local news and business journals.**
Regional outlets cover warehouse openings in detail, usually with square
footage and month. Good coverage of the smaller delivery stations that
national sources miss.

**Option C — municipal permit records.**
County or city permit portals list industrial building permits with dates and
square footage. Slow, but authoritative and genuinely public.

**Option D — published industry inventories.**
Supply-chain consultancies maintain facility lists. ⚠️ **Check the terms of
use before using one.** A commercial firm's compilation may be published but
not licensed for redistribution — and our whole argument is that every source
is free and re-downloadable by a stranger. If the terms do not permit it, use
it only to *find* facilities, then cite the underlying primary source in
`source_url`.

### How many, and which

**Minimum viable: 300–400 facilities** across the ten pilot metros, 2018–2025.
That is enough to fit the hazard model and run the backtest.

**Better: 800+**, weighted toward delivery stations rather than large
fulfilment centres — the small ones are what the model is actually predicting
and are the most under-reported.

The ten metros: San Francisco Bay Area, New York, Chicago, Austin, Seattle,
Denver, Miami, Nashville, Phoenix, Boise.

> **On dates being approximate:** "opened sometime in 2024" is useful. Put
> `open_year=2024` and leave `open_quarter` blank. We model at quarterly grain
> and run a label-noise simulation that reports how much accuracy degrades at
> a given error rate — so an honest blank is far better than a guess.

### Splitting the work

This is the natural place for all three of you to contribute — two metros
each, one shared spreadsheet, then export to CSV. It is also the task that
produces the open dataset, which is the most durable artefact of the project.

---

## 3. Zillow ZORI and ZHVI 🔒

The rent and value indices. Monthly, so they carry the currency argument in
§4.2, and they proxy commercial land cost — the largest capital bucket.

**Steps**

1. Go to **https://www.zillow.com/research/data/** *(blocked from my machine;
   navigate there yourself)*
2. Scroll to **"Rentals"** → **ZORI (Smoothed, Seasonally Adjusted)**.
3. Set **Geography = ZIP Code**, then download the CSV.
   Expected filename: `Zip_zori_uc_sfrcondomfr_sm_month.csv` (~15–25 MB)
4. Scroll to **"Home Values"** → **ZHVI All Homes (SFR, Condo/Co-op)**,
   Geography = **ZIP Code**. Download.
   Expected filename begins `Zip_zhvi_uc_sfrcondo_tier_...` (~25–40 MB)

**Place them**

```
  data/external/zillow_zori/Zip_zori_uc_sfrcondomfr_sm_month.csv
  data/external/zillow_zhvi/Zip_zhvi_uc_sfrcondo_tier_....csv
```

**Licence note:** free for non-commercial research with attribution. That fits
an academic capstone. Keep the attribution line in the data card.

---

## 4. EPA EJScreen 🔒

Environmental-justice indicators. Powers the equity overlay — the deliverable
that makes this a public-interest tool rather than an operator tool.

**Steps**

1. Go to **https://www.epa.gov/ejscreen** and find **"Download EJScreen
   Data"**. ⚠️ The old `gaftp.epa.gov` paths now return 404 and I could not
   confirm the replacement from here, so navigate from the landing page.
2. Choose the most recent year available.
3. Download the **census tract**, national, percentile file. Tract grain
   aggregates cleanly up to ZCTA; block-group is finer than we need and much
   larger.
4. Expect a `.csv.zip` or `.gdb.zip`, roughly 300 MB–1.5 GB.
   **The CSV is what I need** — skip the geodatabase if both are offered.

**Place it**

```
  data/external/ejscreen/<original filename>.zip
```

If only a geodatabase is available, tell me and I will adapt the loader.

---

## 5. BLS OES metro wages 🔒

Driver and warehouse wages by metro. Wages are the second-largest capital
bucket and vary enormously — unionised New York against non-union Austin is
the biggest single cross-metro cost difference in the model.

**Steps**

1. Go to **https://www.bls.gov/oes/tables.htm** *(returns 403 from my machine
   even with a descriptive User-Agent — a browser will work fine)*
2. Pick the most recent year.
3. Download **"All data"** for **Metropolitan and nonmetropolitan area**.
   Expected filename like `oesm23ma.zip` (~50–90 MB)

**Place it**

```
  data/external/bls_oes/oesm23ma.zip
```

**Occupations I use** (I extract these; you do not need to filter):
`53-3033` light truck drivers · `53-7062` labourers and material movers ·
`53-1047` first-line supervisors of transportation and material moving.

---

## 6. EIA energy prices 🔒

Regional fuel and industrial electricity prices. Smallest item on the list —
if you skip it I will use a national constant and say so in the limitations.

**Steps**

1. Register for a free key at **https://www.eia.gov/opendata/register.php**
   *(host returns 403 from here; a browser will work)*
2. Either send me the key the same way as the Census key, **or**
3. Use the browser interface at **https://www.eia.gov/electricity/data.php**
   and export: *Average retail price of electricity, industrial sector, by
   state, monthly*.

**Place it**

```
  data/external/eia_prices/<export>.csv
```

---

## How to hand it all over

Once files are in place, run this from the repo root — it tells you exactly
what I will and will not be able to read:

```bash
cd siting-atlas
.venv/bin/python -m siting_atlas.ingest.external --check
```

It prints one line per source: found or missing, file size, row count, and
whether the columns match what the loader expects. Paste that output to me,
or just tell me the files are in place and I will run it.

If a file fails validation the message says which column is wrong — it is
usually leading zeros stripped from a ZIP code by a spreadsheet. See the
warning below.

---

## The one mistake that will cost you an afternoon

**Excel and Google Sheets silently strip leading zeros from ZIP codes.**
`01890` becomes `1890`, which matches no ZCTA and fails the join.

When you save the facility panel:

- Format the `zip` column as **Text** *before* typing or pasting into it, or
- Export from Sheets with **File → Download → CSV** after setting the column
  format to *Plain text*, or
- Prefix each ZIP with an apostrophe (`'01890`) while editing.

The validator checks for this specifically and will tell you if it happened.

---

## Summary checklist

```
  [ ] 1  Census API key        -> paste in chat, or .env       (5 min)
  [ ] 2  Facility panel CSV    -> data/external/facility_panel/ (hours)
  [ ] 3  Zillow ZORI + ZHVI    -> data/external/zillow_*/       (5 min)
  [ ] 4  EJScreen tract CSV    -> data/external/ejscreen/       (10 min)
  [ ] 5  BLS OES metro zip     -> data/external/bls_oes/        (10 min)
  [ ] 6  EIA prices            -> data/external/eia_prices/     (10 min)

  then:  .venv/bin/python -m siting_atlas.ingest.external --check
```

Items 1 and 2 are the ones that matter. Everything else degrades gracefully,
and the pipeline reports exactly what it fell back to rather than hiding it.
