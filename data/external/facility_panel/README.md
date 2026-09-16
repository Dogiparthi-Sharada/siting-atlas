# data/external/facility_panel — the TARGET VARIABLE

The most important directory in `data/`. Everything else is a covariate; this
is the thing the models try to predict. [`../README.md`](../README.md) covers
`external/` as a whole and
[`../../README.md`](../../README.md) covers `data/`.

## What is here

```
  facilities.csv                       43 rows   SHIPS. The pilot panel,
                                                 10 metros
  national_facilities.csv             104 rows   SHIPS. The national pilot
                                                 frame
  national_facilities_expanded.csv    693 rows   exempted from .gitignore,
                                                 currently untracked
  geocoded_expanded.csv               693 rows   Census Batch Geocoder output
                                                 for those rows: 501 Match,
                                                 190 No_Match, 2 Tie
  TEMPLATE.csv                                   the column stub. Local only
```

Same schema across the three facility CSVs: `facility_id, operator,
facility_type, city, state, zip, latitude, longitude, open_year, open_quarter,
square_feet, status, source_url, source_type, confidence, metro_label,
in_fitting_metro, priority, osm_name`.

## Why two of them ship when the rest of `external/` does not

They were **assembled by hand** across several sessions of classification
batches against OSHA records, press releases and permit filings. No URL
returns them. 22 KB combined, and losing them loses the project. The exemption
and its reasoning are in `.gitignore`.

`national_facilities_expanded.csv` is the 693-row frame the current results
are fitted on. It is exempted too, but **it is not committed today** — so a
clone reproduces the 104-facility results, not the 693-facility ones.
`docs/NUMBERS.md` §1 records this.

## Provenance — read this before trusting a row

How each label was produced, verified and in six cases falsified is in
[`../../collection/README.md`](../../collection/README.md) and
[`../../../docs/data/FACILITY_PANEL_PROVENANCE.md`](../../../docs/data/FACILITY_PANEL_PROVENANCE.md).

Two facts that change how the panel can be used: most dates are OSHA-derived
**upper bounds** rather than opening dates, and OSHA inspects where people get
hurt, so the source sees fulfilment centres far better than the delivery
stations the model is about. Measured in
[`../../../docs/data/DATA_QUALITY.md`](../../../docs/data/DATA_QUALITY.md).

Validate anything you place here:

```bash
python -m siting_atlas.ingest.external --check
```
