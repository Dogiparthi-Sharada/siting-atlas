# common — the cross-cutting layer

Everything every other package depends on: where files live, who is running,
what got logged, how a database statement or an HTTP request is made, and
how two free-text addresses are compared. Nothing here is analysis.

**Start here:** `paths.py`. It names the layers (L0-L4) that the rest of the
codebase and the documentation both use, and it is nine lines of docstring.
Then `logging_setup.py` if you are trying to work out where a run's output
went.

---

## Files

```
  file                purpose                                    state
  ------------------  -----------------------------------------  -------
  __init__.py         package note. Says configure() should be   current
                      called once by the entry point first
  paths.py            the canonical filesystem layout. Every     works
                      module resolves paths through here, so
                      the pipeline relocates with one env var
                      (SITING_ATLAS_ROOT)
  config.py           credentials from the environment, with a   works
                      gitignored .env loaded automatically;
                      plus vintages, the metro list and
                      modelling constants in one place
  context.py          ambient run context (run id, layer,        works
                      stage) in contextvars, stamped onto
                      every log record. Note the documented
                      limit: a threading.Thread does NOT
                      inherit it
  logging_setup.py    one human console stream plus segregated   works
                      machine streams under logs/run-<id>/:
                      console.log, events.jsonl, sql.jsonl,
                      commands.jsonl, http.jsonl, errors.log
  log_json.py         write_json() for result artefacts,         works
                      stamped with the run that produced them.
                      Kept out of logging_setup so writing a
                      metrics file does not drag in handlers
  trace.py            traced_layer / step / artefact / metric.   works
                      Crossing a pipeline boundary is never
                      implicit, so a failed run shows how far
                      it got
  db.py               DuckDB access. No module opens its own     works
                      connection; going through connect() puts
                      every statement in sql.jsonl with its
                      parameters, timing and row count
  http.py             HTTP with retries, a content-addressed     works
                      cache under data/raw/<source>/<sha>.<ext>
                      and full request logging. _scrub() lives
                      here and is why a key no longer reaches
                      a log
  shell.py            subprocess execution with argv, cwd,       works
                      exit code, duration and an output tail
                      recorded in commands.jsonl
  seeds.py            the single source of random seeds, read    works
                      from reproducibility/seeds.toml and
                      cached. Nothing hardcodes a seed
  metros.py           the pilot metros keyed to stable CBSA      works
                      codes. Exists because substring matching
                      on a metro name silently enlarges the
                      sample ("Austin" also matches Austin, MN)
                      and because six of eleven CBSA TITLES
                      changed between the 2020 and 2023
                      delineations
  address.py          standardise and parse a US street          works
                      address into components in FIXED
                      LOCATIONS (Winkler RR99-04 2.3). A
                      separate step that runs before
                      comparison, not a helper inside a matcher
  address_tables.py   the standardisation vocabulary itself -    works
                      suffixes, directionals, unit designators.
                      Split out so the tables can be reviewed
                      on their own. One table for the whole
                      project; there used to be two that
                      disagreed
  linkage.py          decides whether two facility records are   works
                      the same building. Implements
                      Fellegi-Sunter's THREE-way rule (match /
                      non-match / clerical review) but
                      deliberately NOT the likelihood ratio -
                      the reasoning is in the docstring and it
                      cites the paper
  linkage_group.py    turns pairwise verdicts into groups        works
                      without inventing merges. The transitive
                      closure is CHECKED, not trusted: a
                      component containing an explicitly
                      rejected pair is rebuilt from strong
                      edges only
```

## Worth knowing

`http._scrub` and the parameter redaction in `db.py` exist because of a real
incident, not a hypothetical one: a live `EIA_API_KEY` reached
`console.log`, `events.jsonl` and `errors.log` at once, because `requests`
puts the fully expanded URL into its exception message and the retry path
logged that exception verbatim. `logs/` is gitignored and
`scripts/check_no_secrets.py` is the last gate before the index.

`linkage.py` and `linkage_group.py` are the reason the facility panel has
101 buildings rather than some other number. They pair the three contested
Tracy/Hawthorne/Portland records at score 1.000 with no false positives —
the identity is not in doubt, the OPENING DATES are. See
`docs/data/DATA_QUALITY.md`.

Nothing here is generated; every file is hand-written source.
