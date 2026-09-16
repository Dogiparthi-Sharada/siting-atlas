# data/external/nlrb — union petitions as a second sighting of the network

The NLRB publishes petitions and elections by employer and address. The
project uses them not as a labour outcome but as an **independent list of
Amazon buildings**: two incomplete lists of the same population measure each
other, which is how
`outputs/metrics/nlrb_coverage.json` estimates how many facilities the primary
source never sees. [`../README.md`](../README.md) covers `external/`.

## What is here

```
  nlrb_cases_amazon.csv                      SHIPS, 877 KB. Cases filtered
                                             to Amazon across six spellings
                                             of the company name
  HOWTO.md                                   SHIPS. How the export was made
  nlrb_elections_TRUNCATED_unfiltered.csv    local only. The raw election
                                             export before filtering, and
                                             truncated by the site's result
                                             cap -- the name says so
  TEMPLATE.csv                               the column stub. Local only
```

## Why the cases file ships when the rest of `external/` does not

It is a filtered export from an **interactive search that caps results and has
no stable query URL**. Reproducing it means redoing the search under six
spellings of the company name by hand. Small, irreplaceable, and exempted in
`.gitignore` with that reason.

`HOWTO.md` is the procedure for redoing it anyway. Read it before re-fetching;
the name matching is the whole difficulty. See also
[`../../../docs/data/NLRB.md`](../../../docs/data/NLRB.md).

Validate anything you place here:

```bash
python -m siting_atlas.ingest.external --check
```
