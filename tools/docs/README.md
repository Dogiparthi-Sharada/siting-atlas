# tools/docs

Covered by [`../README.md`](../README.md) — read that first.

One utility now. `md_to_txt.py` was deleted on 2026-09-16 along with the 113
`.txt` twins it produced; do not add it back (`scripts/build_all.sh` explains
why in its "missing fourth stage" note).

```bash
python tools/docs/gen_data_docs.py
```

Regenerates `docs/data/README.md` and one `docs/data/<source>.md` page per
data source, from `src/siting_atlas/ingest/sources.py` and the last
`outputs/metrics/source_probe.json`. Generated rather than hand-written so the
licence, endpoint, grain and measured reachability in the docs are the same
values the pipeline actually uses.

**It overwrites hand edits.** `docs/data/README.md` currently carries a
hand-corrected sentence that the next run will revert — the file says so at the
top. Fix the registry, not the output.
