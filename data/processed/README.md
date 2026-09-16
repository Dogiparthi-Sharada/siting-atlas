# data/processed — L2/L3 output: the frame every model reads

[`../README.md`](../README.md) covers the tree as a whole. This layer is the
end of the data pipeline: the DuckDB star schema and the panels built from it.

## What ships

```
  panel.parquet   15 MB. The pilot ZCTA-quarter panel.
  README.md, .gitkeep
```

`panel.parquet` is exempted by name at the bottom of `.gitignore`, and it is
the reason a stranger can run anything at all. With it present:

```bash
make reproduce     # cost, model, scope, figures -- no network, no API keys
```

## What is here on a working machine

```
  panel.parquet            pilot facility frame
  panel_expanded.parquet   the 693-row expanded frame -- what the current
                           results are fitted on
  panel_national.parquet   the national frame
  siting_atlas.duckdb      27 MB star schema. Excluded by the repo-wide
                           *.duckdb rule; it is a build product of the
                           parquets, not a source
```

All three panels are 1,081,312 rows x 50 columns. That is not a copy: the
grain is ZCTA x quarter and the facility frame sets only the target column.
Read `outputs/metrics/panel_report*.json` for their `target` blocks, not their
row counts.

**`panel_expanded.parquet` does not ship.** It is 15 MB and would fit, but it
is derived from `national_facilities_expanded.csv`, which is itself untracked
— so the 693-row panel exists only on the machine that built it. Rebuild it
with `make warehouse && make panel` once the expanded facility CSV is present.

## Rebuilding

```bash
make warehouse    # parquet -> the DuckDB star schema
make panel        # the ZCTA-quarter panel, --facility-frame {pilot,national,expanded}
```

A hand edit here is lost at the next run.
