# .github — continuous integration and the contribution templates

```
  workflows/ci.yml          the only workflow
  PULL_REQUEST_TEMPLATE.md  the PR checklist
  ISSUE_TEMPLATE/           two forms: a new data source, an analytical finding
```

## When CI runs

On **push to `main`** and on **pull requests targeting `main`**. Nothing else
triggers it — no schedule, no tags, no other branch. Concurrent runs on the
same ref cancel each other.

## The four jobs

| job | what it proves |
|---|---|
| `lint` | `ruff check src tests`. `tools/` is excluded on purpose (`make lint-tools` runs it on demand) |
| `test` | the full pytest suite with coverage, run with `SITING_ATLAS_ROOT` pointed at an **empty directory** — so a green tick means the tests test the code and not somebody's warm data cache |
| `smoke` | the package imports from outside the repo root; every module the Makefile names really exists and has a `main()`; then, only if a cached source tree is present, the whole L1→L5 pipeline is run for real |
| `documents` | the pre-registration seal gate (below), then builds the figures, the proposal and both decks and runs `check_layout.py` on each deck |

## Why several steps are gated rather than allowed to fail

`data/` is gitignored, so a checkout has no inputs beyond
`data/raw/manifest.jsonl`. The API keys (`CENSUS_API_KEY`, `EIA_API_KEY`) are
repository secrets and are absent on fork pull requests. Rather than let those
steps go red for reasons a contributor cannot fix, `smoke` checks for the keys
and for a warm cache first and prints a `::notice::` when it skips. **The L0
fetch is skipped, not faked.**

## The pre-registration seal gate

This is the unusual one, and it is the first step of the `documents` job:

```bash
recorded=$(python -c "import json;print(json.load(
    open('outputs/metrics/metro_entry.json'))['prereg_md5'])")
actual=$(md5sum docs/PREREG_METRO_MODEL.md | cut -d' ' -f1)
test "$recorded" = "$actual"
```

`docs/PREREG_METRO_MODEL.md` fixed the hypothesis, the arms and the success
criterion **before** the metro entry model was fitted. The md5 of that file at
fit time is recorded inside the result artefact. If the two ever disagree,
either the pre-registration was edited after the result was known or the
artefact came from a different pre-registration — and the claim to having
pre-registered anything evaporates. So CI fails the build instead.

Both currently read `946f7ef75db69e5278eea409a04c3823`.

Consequences worth knowing before you touch either file:

* **Do not edit `docs/PREREG_METRO_MODEL.md`.** Corrections go in
  `docs/PREREG_METRO_MODEL_ERRATA.md`, which is deliberately *not* covered by
  the hash — so a correction is visible as a separate document rather than
  disguised as the original.
* If the seal is genuinely broken, restore it from the byte-exact copy in
  [`../reproducibility/seals/`](../reproducibility/seals/) rather than
  re-deriving it.
* Re-running `make metro` rewrites `prereg_md5` from whatever is on disk at
  that moment, so re-running is not a fix — it is how a broken seal becomes an
  invisible one.

## Templates

`PULL_REQUEST_TEMPLATE.md` is a checklist (lint, tests, document build, no
data committed, seeds from `reproducibility/seeds.toml`, an ADR if the
decision is expensive to reverse). `ISSUE_TEMPLATE/data_source.md` asks the
one question that decides admission — *free, public, and re-downloadable by a
stranger?* — and `ISSUE_TEMPLATE/finding.md` asks for the claim affected and
the evidence.

## One stale comment

The header comment in `ci.yml` still describes diffing `.txt` twins of the
Markdown documents. Those twins and their generator were deleted on
2026-09-16; no CI step diffs them today.
