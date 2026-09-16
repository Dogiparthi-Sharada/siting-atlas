# data/interim — L1 output: one typed parquet per source

Derived, and almost all of it is gitignored because it is re-derivable in
minutes from [`../raw/`](../raw/) and [`../external/`](../external/).
[`../README.md`](../README.md) covers the tree as a whole.

## What ships

```
  cbp_detail.parquet       County Business Patterns, ZIP x NAICS. 1.1 MB.
                           Exempted because re-deriving it means ~120 MB of
                           downloads across seven vintages
  mwpvl_facilities.csv     the 1,904 facilities OCR'd out of the MWPVL
                           article, attributed to MWPVL International.
                           Exempted because the source PDF cannot be
                           redistributed and is being withdrawn from
                           circulation -- these facts are what survives it
  README.md, .gitkeep
```

Both are exempted by name at the bottom of `.gitignore`, with the reason.

## What is here on a working machine (~620 MB)

One typed parquet per normalised source — `acs5_zcta_2023`, `bls_wages`,
`building_permits`, `cbp`, `cbsa_county`, `eia_energy`, `ejscreen_tract`,
`gazetteer`, `highway_access`, `osm_landuse`, `tiger_interchanges`,
`zcta_county`, `zcta_geom`, `zillow_zhvi`, `zillow_zori`, `acs1_metro_2023` —
plus the hand-assembled CSVs `osha_amazon.csv` and `nlrb_amazon.csv`, and a
`prepromotion_backup/` of the frames as they stood before a panel promotion.

`zcta_geom.parquet` alone is 526 MB.

## Rebuilding

```bash
make normalise            # from data/raw
make normalise-external   # from data/external
```

**A hand edit here is lost the next time the stage runs.** Two warnings from
the parent README apply hardest at this layer: ZIP codes are zero-padded
strings, always (`ingest/shapes.py:_zpad`), and Excel strips leading zeros on
save.
