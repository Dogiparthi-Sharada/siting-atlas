# data/raw — the download cache. Almost none of it ships.

If you cloned this repository and found one file here, nothing is broken.
[`../README.md`](../README.md) explains the tree; this note covers what
`raw/` specifically would hold.

## What is here in a clone

```
  manifest.jsonl   the provenance record: URL, SHA-256, byte count and
                   content type for every automatic download the project has
                   ever made. 16 KB. THE thing to read if you want to know
                   where a byte came from
  README.md        this file
  .gitkeep
```

## What is here on a working machine

One directory per registry key — 19 of them, ~3.7 GB:

```
  acs1_2023  acs5  acs5_2023  bps_county  cbp_zip  cbp_zip_detail
  cbsa_county  eia_diesel  eia_electricity  eia_prices  gaz_zcta
  geofabrik  mwpvl  osha_bulk  osm_amazon  osm_landuse  tiger_roads
  tiger_zcta  zcta_county_xwalk
```

Publisher filenames, unmodified, archives left zipped — the pipeline reads
them as downloaded and the checksum of the original goes in the manifest.

## Why it does not ship

Mostly size. `osha_bulk` is 1.4 GB, `tiger_roads` 1.6 GB, `tiger_zcta`
528 MB, `cbp_zip_detail` 119 MB; four files exceed GitHub's 100 MB per-file
limit. All of it is **free and re-downloadable**, which is the rule the whole
project obeys.

One exception is not about size. `mwpvl/*.pdf` is third-party copyright and
the publisher is withdrawing the article from free circulation, so it is
excluded deliberately and permanently. The **facts** extracted from it do ship,
attributed, as `data/interim/mwpvl_facilities.csv`.

## Getting it back

```bash
make acquire        # needs the network and CENSUS_API_KEY + EIA_API_KEY
```

Per-source URLs, commands, keys, sizes, licences and vintages are in
[`../../docs/DATA_SOURCES.md`](../../docs/DATA_SOURCES.md). Read its final
section first: most of the headline results rebuild from what is already in
your clone, with no downloads at all.
