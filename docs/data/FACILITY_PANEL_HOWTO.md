# How to build the facility panel — step by step

**The target variable. Two hours gets you a usable first version.**

> **Status, 2026-09-13: the panel has been built. This page is the brief that
> started it, kept because it is still the fastest route for anyone adding a
> new metro.** `data/external/facility_panel/facilities.csv` now holds 43
> Amazon delivery stations and `ingest.external --check` passes. What
> actually produced those rows was not only the two jobs below: Job 1
> (OpenStreetMap) gave locations and Job 2 (hand search) dated 16 of the 43
> rows — those are the ones whose `site_address` reads `(osm)`. The other 27
> carry a real street address and were dated from the **US DOL OSHA bulk
> inspection extract**, which yields an "operating by" upper bound rather
> than an opening date. Read
> [`FACILITY_PANEL_PROVENANCE.md`](FACILITY_PANEL_PROVENANCE.md) before you
> add a row, so that what you add is consistent with what is already there.

The trick is to split it into two jobs that are each easy, instead of one job
that is hard:

```
  JOB 1   WHERE are the facilities?   -> automated, ~5 min per state
  JOB 2   WHEN did each one open?     -> manual, ~1 min per facility
```

Job 1 is a browser tool with a query I have already tested. Job 2 is the only
part that needs a human, and it is fast because Job 1 hands you the facility's
own internal code, which is what news coverage names.

---

## Job 1 — get the facility inventory (5 minutes per state)

OpenStreetMap has these buildings mapped with operator, address and postcode.
You can export them from a browser with no account and no installation.

### Steps

1. Open **https://overpass-turbo.eu**

2. Delete whatever is in the left-hand code box and paste this:

```
[out:json][timeout:120];
area["ISO3166-2"="US-AZ"][admin_level=4]->.a;
(
  nwr["operator"~"Amazon",i]["building"](area.a);
  nwr["operator"~"Walmart",i]["building"="warehouse"](area.a);
  nwr["operator"~"Costco",i]["building"="warehouse"](area.a);
  nwr["operator"~"Target",i]["building"="warehouse"](area.a);
);
out center tags;
```

3. Change **`US-AZ`** to the state you want. The ten pilot metros need:

   `US-CA` `US-NY` `US-IL` `US-TX` `US-WA` `US-CO` `US-FL` `US-TN` `US-AZ` `US-ID`

4. Click **Run** (top left). Wait 10–60 seconds.

5. Click **Export** → **raw data directly from Overpass API**. It downloads a
   `.json` file. Save it as `osm_CA.json`, `osm_NY.json` and so on.

6. Repeat for each state. Ten states, about five minutes total.

**Send me the ten JSON files.** I will convert them into the CSV columns,
attach the ZIP codes, infer the facility type from the station code, and hand
you back a spreadsheet where the only empty column is `open_year`.

> **Coverage warning, so you are not surprised.** OSM is crowd-sourced and
> coverage is uneven — Arizona returned 30 facilities, Tennessee returned 1.
> Expect a strong yield in CA, TX, IL, NY and a weak one in TN, ID. Job 1 gets
> you maybe 60% of the facilities for 5% of the effort; the rest come from
> Job 2's searching anyway.

---

## Job 2 — find the opening year (about 1 minute each)

This is the part only a person can do, and the station code makes it quick.

### Why the code matters

Amazon names every building with an internal code — `DAX5`, `PHX6`, `DTU8`.
Local news and trade press use those codes, so they are far better search
terms than an address.

You can also read the type straight off the code:

| Pattern | Type | Put in `facility_type` |
|---|---|---|
| Starts with **D** — `DAX5`, `DTU8`, `DLX7` | Delivery station | `DS` |
| Airport code + digit — `PHX6`, `BFI4`, `DFW7` | Fulfillment centre | `FC` |
| Contains **SSD** or starts **S** | Same-day site | `SDC` |
| Starts **XL** or contains **AMXL** | Oversize | `AMXL` |
| Sort centre — often `...S1`, `...S2` | Sortation | `SC` |

If you cannot tell, put `DS` — delivery stations are the large majority and
the model cares far more about *where and when* than about the exact type.

### The search that works

For each facility, search:

```
"DAX5" Amazon Hayward opened
"Amazon DAX5" delivery station
Amazon delivery station <city> <state> opened
```

You are looking for one sentence in a news story or press release:
*"the facility opened in March 2024"* or *"began operations last fall."*

**Record the year. Leave the quarter blank unless the article states a month.**
A blank quarter is honest; a guessed quarter is noise I cannot detect.

### When you cannot find a date

Skip it — do not guess. Leave the row out entirely, or set `status=open` and
leave `open_year` blank and I will drop it. A facility with no date cannot
train the model, and an invented date actively damages it.

---

## What "done" looks like

| Target | Facilities | What it buys |
|---|---|---|
| **Minimum** | 50, one metro | I can build and validate the whole L4 backtest end to end |
| **Workable** | 300 across 10 metros | A real backtest with a defensible AUC |
| **Good** | 800+, delivery-station weighted | Publishable, and the open dataset becomes the durable artefact |

**Start with 50 in one metro.** Pick whichever metro one of you knows best —
the Bay Area or Phoenix are well covered in OSM. That unblocks me completely
and you will learn how long 50 actually takes before committing to 300.

---

## Splitting it three ways

The natural division, and it maps onto the roles already in Section 6:

```
  P1   Bay Area, Seattle, Denver        (dense OSM coverage)
  P2   New York, Chicago, Austin        (heavy news coverage)
  P3   Phoenix, Miami, Nashville, Boise (thinner - more searching)
```

One shared Google Sheet, one tab each, export to CSV at the end.

---

## The one mistake that will cost you an afternoon

**Format the `zip` column as Text before you type in it.**

Excel and Google Sheets strip leading zeros: `01890` silently becomes `1890`,
which matches no ZCTA, and the join drops the row without an error.

- Google Sheets: select column → Format → Number → **Plain text** *first*
- Excel: select column → Format Cells → **Text** *first*
- Or type an apostrophe before each: `'01890`

My validator checks for exactly this and will tell you if it happened, but it
is much easier to avoid than to repair.

---

## Checking your work

Drop the CSV at `data/external/facility_panel/facilities.csv` and run:

```bash
cd siting-atlas
.venv/bin/python -m siting_atlas.ingest.external --check
```

It reports the row count, the year range, how many operators, how many rows
carry a quarter, and any ZIP damage. Paste me the output, or just tell me it
is there.

---

## Summary

```
  [ ] 1  overpass-turbo.eu, run the query for 10 states   (~5 min)
  [ ] 2  send me the 10 JSON exports                      (~1 min)
  [ ] 3  I return a CSV with only open_year empty
  [ ] 4  fill open_year by searching the station codes    (~1 min each)
  [ ] 5  drop the CSV in and run --check
```

Steps 1–3 cost you six minutes and remove most of the work. Step 4 is the
real task, and 50 rows is enough to start.
