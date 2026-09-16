# outputs — everything the pipeline emits

L4/L5 artefacts. **Every file under this tree is GENERATED.** A hand edit
survives until the next run of the stage that wrote it, and then it is gone
without a warning. If a number here is wrong, fix the code, not the file.

**Start here:** [`metrics/README.md`](metrics/README.md) — 30 JSON artefacts,
one line each, with the command that regenerates it. Every result the project
has is in that directory.

---

## The directories

```
  dir        holds                              written by       index
  ---------  ---------------------------------  ---------------  --------------
  metrics/   30 JSON reports                    every stage      metrics/README.md
  tables/    8 parquet result tables            cost, retired    tables/README.md
                                                stages
  figures/   20 PNGs, 4 charts x 5 scenarios    viz.build        figures/README.md
  logs/      one long console capture from the  by hand          --
             500-draw Monte Carlo
  audit/     EMPTY -- the agent that wrote it   nothing, today   --
             was retired to experiments/
  models/    EMPTY -- no serialised model is    nothing, today   --
             written; a placeholder for a
             specification that does not exist
  scratch/   EMPTY -- paths.SCRATCH, where      nothing, today   --
             long searches write resume
             checkpoints while they run
```

`audit/`, `models/` and `scratch/` are empty directories and will not survive
a clone.

## Source of truth

When a document and an artefact disagree, the artefact wins — and
[`../docs/NUMBERS.md`](../docs/NUMBERS.md) is the tie-breaker that was
re-derived from the artefacts directly. The long-form account of every JSON
file, its stamping status and the known cross-artefact disagreements is
[`../docs/data/ARTEFACTS.md`](../docs/data/ARTEFACTS.md).

## Regenerating the lot

```
  make reproduce   cost, model, scope, figures - the headline results,
                   offline, no API keys, from the two data files that ship
  make all         normalise, normalise-external, warehouse, panel, cost,
                   model, scope, figures - the whole offline pipeline
```

`acquire` needs credentials and the network, `app` blocks on a server, `metro`
is a one-off pre-registered test and `covariates` runs for about ninety
minutes, so all four sit outside `make all` on purpose.
