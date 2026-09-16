# Contributing

## Principles

1. **Every claim must be checkable.** If a number appears in the documentation,
   the code that produced it is in the repository.
2. **Contracts fail the build.** A data contract is not a warning.
3. **Never commit raw data.** `data/` is gitignored and re-derivable from
   `data/raw/manifest.jsonl`. Two derived files are deliberate exceptions and
   are un-ignored by name — `data/processed/panel.parquet` and
   `data/interim/cbp_detail.parquet` — because without them a clone cannot
   reproduce anything without ~4 GB of downloads and three API keys.
4. **Seeds live in `reproducibility/seeds.toml`.** Nothing hardcodes one.
5. **Some documentation is generated** — `docs/figures/*.png`,
   `docs/data/README.md` and `docs/data/<source>.md`. Edit the generator in
   `tools/`, not the output. The plain-ASCII `.txt` twins that used to sit
   beside every `.md` have been **removed and are not being restored**. The
   generator that produced them, `scripts/build_docs.sh`, and its renderer
   `tools/docs/md_to_txt.py`, were deleted with them -- leaving the generator
   callable would mean the next `make docs` silently recreated all 113.

## Working with numbers

This is the rule the project has had to relearn most often, so it gets its own
section.

1. **Cite the artefact, not the figure.** Every headline number is emitted to
   `outputs/metrics/*.json` with a `run_id`. Quote the `run_id`; a number typed
   into prose is a convenience and it will drift. Several published headlines
   have been invalidated by re-running the code that produced them, and not one
   of those moves was caused by a parameter.
2. **[`docs/NUMBERS.md`](docs/NUMBERS.md) is the tie-breaker.** It re-derives
   every headline figure from its artefact and names the stale variants. If a
   document and `NUMBERS.md` disagree, `NUMBERS.md` wins and the document is
   the bug.
3. **Name the quantity fully.** Four artefacts publish something called a
   "large-metro top-10 lift" on four different frames. Always name arm *and*
   method *and* artefact.
4. **A percentile over re-splits is not a confidence interval.** Several
   artefacts carry a `spread_is_not_a_standard_error` field saying so. Writing
   "95% CI" over one of them is wrong.
5. **If a number is measured by hand, say so** — and then make the emitter
   print it. Every hand-counted figure in this project's history has moved at
   least once.

## If you are an AI agent working on this repository

Read [`docs/STATUS.md`](docs/STATUS.md) and
[`docs/NUMBERS.md`](docs/NUMBERS.md) in full, then the README of whichever
folder you are about to touch. Three standing rules, all learned the hard way
and all recorded in [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md):

- **Verify the numbers in your brief. They have been wrong before.** An agent
  that rebuilt a chain and contradicted its instructions has been right more
  often than the instructions.
- **Report defects, do not silently fix them.** Especially anything that moves
  a published figure. The habit of writing the defect down is why this project
  can be defended at all.
- **Do not delete a correction.** When a claim is wrong, this repository
  records what it used to say and why it changed, rather than quietly editing.
  A correction that goes against the project is worth more than one that
  flatters it.

**Rule of thumb on the tree:** anything under `outputs/` is generated and hand
edits are lost. Anything under `data/external/` was placed by hand and cannot
be regenerated.

## Before opening a pull request

```bash
make lint          # ruff + black --check
make test          # pytest
bash scripts/build_all.sh   # figures, proposal, deck, docs - all validated
```

`build_all.sh` fails if a figure label overflows its box, a slide violates the
layout rules, or a generated text file leaves ASCII or exceeds 80 columns.

## Code style

- Python 3.11, 79-column lines, type hints on public functions
- Modules stay under ~300 lines; split rather than grow
- Docstrings say *why*, not *what* — the code already says what

## Architecture decisions

Anything that would be expensive to reverse gets an ADR in `docs/adr/`.
Copy `docs/adr/0000-template.md`.

## Commit messages

Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.

## Adding a data source

1. Extractor in `src/siting_atlas/ingest/`, writing through the cache
2. An entry in the manifest
3. An L1 normaliser producing one typed parquet
4. A data contract
5. A row in the registry table in `docs/data/README.md` and an entry in
   [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md)

A source that is not free, public and re-downloadable by a stranger does not
belong in this project — that constraint is the contribution, not a budget
limit.
