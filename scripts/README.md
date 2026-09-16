# scripts — the launchers

Entry points that are **not** pipeline stages. Anything that IS a pipeline
stage is a module with a `main()` and is invoked through the Makefile
instead; CI asserts that every module the Makefile names is real.

**Start here:** the Makefile at the repo root. It is the index of what you
can run. This directory holds only the handful of things a Makefile target
cannot express.

The MWPVL OCR toolchain used to live here, under `scripts/grid/`, alongside
three shell scripts that relocated tesseract, glibc and the dynamic loader
onto a locked-down Python 3.6 compute grid. Those were removed on 2026-09-16
as environment-specific -- they solved one institution's problem, not an OCR
one. The OCR itself now lives in [`tools/ocr/`](../tools/ocr/README.md).

---

## The three shell scripts

| script | what it is for | when you would run it | exit codes |
|---|---|---|---|
| `preflight_publish.sh` | Every check that must pass before this repository is pushed in public: leaked secrets, licensed data that must not ship, reproducibility inputs that must ship, the pre-registration seal, GitHub's 100 MB limit, absolute home paths, ruff, and "every module under `src/` imports". Read-only. | Immediately before `git push`, and after any change that moves data files or retires a module. | `0` safe to push · `1` a check failed · `2` bad usage · `3` repo root not found · `4` missing prerequisite (git or python) |
| `build_all.sh` | The document build, in the order that matters: figures, then the proposal, then the decks with a layout check on each. Figures are embedded in both the proposal and the decks, so building them last ships yesterday's charts inside today's document. | Before sending a deliverable, and whenever a figure or `PROPOSAL_V5.md` changes. This is what `make docs` runs. | `0` built and valid · `1` unexpected failure · `2` bad usage · `3` missing prerequisite · `4` a build stage failed · `5` a deck failed its layout check |
| `run_dashboard.sh` | Serves the Streamlit cost-to-serve app. It exists because Streamlit execs the app file with no parent package, so `src/` has to be exported onto `PYTHONPATH` or the absolute `siting_atlas.*` imports fail. Blocks until Ctrl-C. | To look at the cost tables interactively, after `make cost`. This is what `make app` runs. | `0` clean shutdown · `1` unexpected failure · `2` bad usage · `3` streamlit not installed · `4` no cost tables to display |

### Exit codes that changed

If you have these in shell history or a wrapper, three numbers moved so that
`2` could mean the same thing everywhere:

- `preflight_publish.sh`: "cannot find repo root" was `2`, is now `3`.
- `run_dashboard.sh`: "streamlit not installed" and "no cost tables" were
  both `2`; they are now `3` and `4`, so a wrapper can tell "you typed it
  wrong" from "the data is not built yet".

---

## The shared conventions

Every shell script in this directory meets the same standard. If you add one,
copy `preflight_publish.sh` — it is the reference.

**1. A header block.** What the script does, what it needs, what it produces,
every exit code with its meaning, and an example invocation — written for
someone who has never seen this repository.

**2. `set -euo pipefail`**, with any exception documented *in the script*.
There is exactly one: `preflight_publish.sh` omits `-e` deliberately, because
the whole point is that every check runs and you see the complete list of
what is wrong in one pass. Under `-e` the first failing check would abort the
run, turning a thirty-second report into a morning. It collects failures in a
variable and reports them at the end instead.

**3. Runnable from anywhere.** The repo root is resolved from
`${BASH_SOURCE[0]}`, never from `$PWD` and never hardcoded, and **the
caller's working directory is restored by an `EXIT` trap**:

```bash
CALLER_PWD="$PWD"
cleanup() { cd "$CALLER_PWD" 2>/dev/null || true; }
trap cleanup EXIT
```

A trap and not a `cd` at the bottom: a trap also fires when `set -e` aborts
the script mid-way and when the user hits Ctrl-C, which is precisely when
being left in someone else's directory is most confusing.

The trap alone is not sufficient, so each script also **refuses to be
sourced**. A sourced script runs in *your* shell, where an `EXIT` trap fires
when the shell dies rather than when the script ends — so `. build_all.sh`
would hand you back a prompt sitting in the repo root, and
`. preflight_publish.sh` would close your terminal on its final `exit`.
Sourcing is rejected with exit `2` and a one-line explanation. Run them with
`bash`, which is a child process and cannot move your shell at all.

**4. Distinct, documented exit codes.** `0` success, `1` a real but
unexpected failure, `2` bad usage, and named codes from `3` upward for the
specific failure modes that script has. No script exits non-zero without
first saying why.

**5. `--help` / `-h`** prints usage and exits `0`.

**6. `--verbose` / `-v`** turns on `set -x`. **`--dry-run` / `-n`** is
provided by the two scripts with side effects (`build_all.sh`,
`run_dashboard.sh`) and prints what would happen without doing it.
`preflight_publish.sh` has none, because it is read-only — a dry run of it
would be the same run.

**7. Logging.** Four helpers, all writing to **stderr** with a timestamp:

```
20:41:07 INFO repo   /path/to/siting-atlas
20:41:09 OK   ruff clean
20:41:09 WARN dry run -- nothing will be written
20:41:12 FAIL seal BROKEN in docs/PREREG_METRO_MODEL.md -- recorded a1b2, actual c3d4
              restore: cp reproducibility/seals/PREREG_METRO_MODEL.*.md docs/...
```

- `info` / `warn` / `ok` / `fail` log a line; `note` adds an indented
  continuation for a remedy; `die <code> <message>` logs `FAIL` and exits.
- **stderr, not stdout**, so `2>report.txt` captures the whole story and
  progress is visible while the slow checks run. Nothing here writes a
  machine-readable payload to stdout.
- Colour is emitted only when stderr is a terminal, so redirected output does
  not fill with escape codes.
- An error names **the file and the remedy**, not just the failure. "seal
  BROKEN" is useless; "seal BROKEN in `docs/PREREG_METRO_MODEL.md` — restore
  it with `cp reproducibility/seals/...`" is not.

The helpers are duplicated into each script rather than sourced from a shared
library. Each script is then a single file you can copy, mail or run in
isolation, and none of them can be broken by an edit to a file it does not
mention. The block is about twenty lines; the coupling would cost more.

**8. A preflight section.** Before any real work: resolve the repo root,
check the interpreter runs, check every required binary is on `PATH`, check
every required input file exists. A missing `python-pptx` discovered at stage
3 of `build_all.sh` has already cost you the figures and the proposal, and
leaves the tree half-rebuilt.

**9. Idempotence.** `preflight_publish.sh` is read-only. `run_dashboard.sh`
writes nothing. `build_all.sh` overwrites its outputs in place, so it is
idempotent in effect — but **not** byte-for-byte: `.docx` and `.pptx` are zip
containers that embed a build timestamp, so `git diff` shows a change even
when no content moved. Do not read a dirty tree after a rebuild as evidence
that something changed.

**10. Nothing environment-specific.** No absolute paths into anyone's home or
scratch directory, no secrets, and no `rm -rf` of a path built from a
variable that could be empty. `preflight_publish.sh` enforces the first of
those three across every tracked file.

---

## The Python entry points in this directory

These are not launchers and are not held to the shell standard above; each
carries its rationale in its module docstring.

```
  check_no_secrets.py          the pre-commit hook that refuses a run log or a
                               live credential. Three checks - path, literal
                               value, and pattern - because each catches
                               something the other two miss
  make_unlabelled_batches.py   builds classification batches for the OSHA
                               buildings whose establishment name is silent
  ingest_batch.py              joins a finished labelling batch back to its
                               worklist rows, strictly: a missing or
                               unparsable answer is reported, never dropped
  ocr_mwpvl.py                 OCRs the MWPVL facility tables to word
                               COORDINATES rather than text, because table
                               rows wrap and plain text splits a cell
  osha_amazon.py               a thin launcher for
                               `python -m siting_atlas.ingest.osha`. It used
                               to be a second, divergent implementation of
                               the matcher; it now contains none, and must
                               not become a second opinion again
```

To check what the OSHA matcher is doing, run the audit rather than the
launcher:

```
  python -m siting_atlas.ingest.address_audit --sweep
```

Nothing in this directory is generated.
