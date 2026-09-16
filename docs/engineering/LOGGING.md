# Logging and Observability

**What a run records about itself, where it puts it, and how to diagnose a
failure from the artefacts without re-running anything.**

> **The rule this layer exists to enforce:**
> a line in any log file can be traced back to the exact pipeline position
> that produced it. Every record carries a run id, a layer code and a stage
> name, because a timestamp alone tells you when something happened and
> nothing about what was running.

*Everything below was checked against the source in
`src/siting_atlas/common/` and against real log directories under `logs/` on
2026-09-12, re-checked 2026-09-13 (§8.1) and 2026-09-14 (§5, §2.4, §8.1).
Example lines are copied from those runs, not written by hand.
Where a line exceeded 80 columns it is truncated with a trailing `...`;
absolute paths are shortened to `<repo>/`. Nothing else is altered.*

---

## 1. What a run produces

One directory per run:

```
logs/run-<run_id>/
    console.log        every record, plain text, as printed
    events.jsonl       every record as structured JSON
    sql.jsonl          one record per SQL statement
    commands.jsonl     one record per subprocess
    http.jsonl         one record per HTTP request
    errors.log         WARNING and above only
```

`logs/` is not cleaned automatically and each run is a new directory, so the
history of a debugging session survives.

### 1.1 Three of the six are always there; three are conditional

`configure()` in `common/logging_setup.py` installs `console.log`,
`events.jsonl` and `errors.log`. The other three are created by
`logging_setup.sink()`, which is called at **import time** of the module that
owns the stream:

| File | Created by importing | Present when |
|---|---|---|
| `sql.jsonl` | `common.db` | the stage touches DuckDB |
| `commands.jsonl` | `common.shell` | the stage runs a subprocess |
| `http.jsonl` | `common.http` | the stage can make a request |

This is why the directories are not uniform. The L1 normalise run
`logs/run-20260912-075423-335f/` has three files — it only reads parquet. The
L2 schema run `logs/run-20260912-084253-45ab/` has four, adding `sql.jsonl`.
An L0 acquire run has `http.jsonl`.

**An absent file is information, not a defect.** No `sql.jsonl` means the
stage never opened the warehouse.

---

## 2. The six files, one at a time

### 2.1 `console.log` — what a person watching would have seen

Same formatter as the terminal, minus the colour. The format string lives in
`logging_setup.CONSOLE_FMT`:

```
time  level  layer  stage-or-module      message
```

Real lines, from the L1 normalise run:

```
00:54:23 D L1  normalise:gazetteer    step start
00:54:24 I L1  normalise:gazetteer    gazetteer_rows                 33791
00:54:24 I L1  normalise:gazetteer    done in 0.60s
00:54:24 D L1  normalise:cbp          step start
00:54:24 I L1  normalise:cbp          cbp_rows                       35002
00:54:24 I L1  normalise:cbp          done in 0.38s
```

Two things to know about the level column: it is the first letter only
(`D I W E C`), and `console.log` always captures `DEBUG` even when the
terminal was set to `INFO`. The file is the complete record; the terminal is
the summary.

**The timestamp is local time.** `events.jsonl` timestamps are UTC. The same
statement appears as `01:42:53` in `console.log` and
`2026-09-12T08:42:53.866+00:00` in `sql.jsonl`. Correlate on the run id and
the stage, not on the clock.

### 2.2 `events.jsonl` — the same records, machine-readable

One JSON object per line, stable key order. A worked artefact record from the
L1 run:

```
{"ts": "2026-09-12T07:54:24.582+00:00", "level": "INFO",
"run_id": "20260912-075423-335f", "layer": "L1",
"stage": "normalise:gazetteer", "logger": "siting_atlas.trace",
"msg": "wrote data/interim/gazetteer.parquet (1.1MB) rows=33791 cols=5",
"fields": {"event": "artefact",
"path": "<repo>/data/interim/gazetteer.parquet", "bytes": 1174577,
"rows": 33791, "cols": 5}}
```

The `fields` object is present only when a caller passed
`extra={"fields": {...}}`. Everything that matters programmatically carries
an `event` key, and the full vocabulary is small:

| `event` | Emitted by | Means |
|---|---|---|
| `layer_enter` / `layer_leave` | `trace.traced_layer` | a layer boundary was crossed; `leave` carries `seconds` |
| `layer_abort` | `trace.traced_layer` | the layer raised; carries `error` and `traceback` |
| `step_start` / `step_ok` / `step_fail` | `trace.step` | a named unit of work inside a layer |
| `artefact` | `trace.artefact` | a stage wrote a file; carries `path`, `bytes` and whatever the caller added |
| `metric` | `trace.metric` | one measured quantity, as `name` and `value` |
| `checkpoint` | `trace.checkpoint` | a control-flow marker, DEBUG only |
| `sql` / `sql_result` / `db_close` | `common.db` | see 2.3 |
| `command` | `common.shell` | see 2.4 |
| `http` | `common.http` | see 2.5 |

### 2.3 `sql.jsonl` — every statement, with its context

`common.db.connect()` returns a wrapper, not a raw DuckDB connection. No
module opens its own. Every `execute`, `df`, `scalar` and `script` call lands
here with the flattened statement text, the bound parameters, the elapsed
time and the calling context:

```
{"ts": "2026-09-12T08:42:53.866+00:00", "level": "DEBUG",
"run_id": "20260912-084253-45ab", "layer": "L2", "stage": "build:dim_county",
"logger": "siting_atlas.sink.sql", "msg": "sql", "fields": {"event": "sql",
"kind": "scalar", "verb": "SELECT", "db": "data/processed/siting_atlas.duckdb",
"sql": "SELECT COUNT(*) FROM dim_county", "params": null, "seconds": 0.0011,
"error": null, "run_id": "20260912-084253-45ab", "layer": "L2",
"layer_name": "warehouse", "stage": "build:dim_county"}}
```

`verb` is the leading keyword, which is what makes "how many CREATEs did this
stage run" a one-line question. `kind` records which wrapper method was used.
A failed statement keeps the same shape and fills `error`; the statement is
still logged, then re-raised.

Three console behaviours are worth knowing:

- statements faster than `db.SLOW_QUERY_SECONDS` (2.0 s) are logged at DEBUG;
- slower ones are promoted to WARNING and therefore appear in `errors.log`;
- the console preview is cut at `db._PREVIEW` (110 characters). The full text
  only ever exists in `sql.jsonl`.

Closing a connection emits a `db_close` record with the statement count and
total SQL time — a cheap way to notice a stage doing far more work than it
should. The L2 run reports `12 statements in 2.91s (session 3.16s)`.

### 2.4 `commands.jsonl` — every subprocess

`common.shell.run()` never invokes a shell; `argv` is a list and quoting
cannot surprise you. The record carries the exact argv, working directory,
exit code, duration and the last 4,000 characters of each stream:

```
{"ts": "2026-09-12T06:26:56.264+00:00", "level": "DEBUG",
"run_id": "20260912-062655-34fa", "layer": "L0", "stage": "shell",
"logger": "siting_atlas.sink.commands", "msg": "command",
"fields": {"event": "command", "argv": ["echo", "hello from a traced command"],
"cwd": "<repo>", "env_overrides": null, "exit_code": 0, "seconds": 0.011,
"stdout_tail": "hello from a traced command\n", "stderr_tail": "",
"run_id": "20260912-062655-34fa", "layer": "L0", "layer_name": "acquire",
"stage": "shell"}}
```

No stage in the pipeline currently shells out, so this file only appears in
the observability smoke test. It exists for the routing preprocessing that
`DATA_ENGINEERING.md` §10 plans and has not built. **The `dbt` half of that
sentence is dead**: the `dbt/` tree has been deleted, L2 is
`warehouse/schema.py` calling DuckDB in process, and nothing is going to shell
out to `dbt build`.

### 2.5 `http.jsonl` — every request, cached or not

```
{"ts": "2026-09-12T06:30:51.217+00:00", "level": "DEBUG",
"run_id": "20260912-063050-6920", "layer": "L0", "stage": "acquire:gaz_zcta",
"logger": "siting_atlas.sink.http", "msg": "http", "fields": {"event": "http",
"cached": false,
"url": "https://www2.census.gov/.../2023_Gaz_zcta_national.zip",
"source": "gaz_zcta", "status": 200, "bytes": 1013655,
"sha256": "75191ab2d3df...", "seconds": 0.319,
"content_type": "application/zip",
"path": "<repo>/data/raw/gaz_zcta/47939b6e14e21353.zip", "attempt": 1,
"run_id": "20260912-063050-6920", "layer": "L0", "layer_name": "acquire",
"stage": "acquire:gaz_zcta"}}
```

`cached: true` records a cache hit and carries no `status` or `seconds` — a
warm re-run still produces a complete provenance record. `attempt` counts
retries, so a flaky endpoint is visible rather than inferred.

### 2.6 `errors.log` — the first file to open

WARNING and above, plain text, same format as `console.log`. On a clean run
it is zero bytes. That makes triage a one-liner:

```bash
wc -l logs/run-*/errors.log | sort -rn | head
```

---

## 3. Levels and `SITING_ATLAS_LOG_LEVEL`

Standard Python levels. The split that matters:

| Sink | Level | Configurable |
|---|---|---|
| terminal | `INFO` | yes, via `SITING_ATLAS_LOG_LEVEL` or `configure(level=...)` |
| `console.log` | `DEBUG` | no |
| `events.jsonl` | `DEBUG` | no |
| `errors.log` | `WARNING` | no |
| `sql.jsonl`, `commands.jsonl`, `http.jsonl` | `DEBUG` | no |

**The files always capture DEBUG.** Turning the terminal up does not reveal
anything the artefacts did not already have; it only saves you opening a
file. That is deliberate: a failure you cannot reproduce must still be
diagnosable from what the failing run left behind.

```bash
SITING_ATLAS_LOG_LEVEL=DEBUG PYTHONPATH=src \
  .venv/bin/python -m siting_atlas.ingest.normalise
```

Unrecognised values fall back to `INFO` rather than raising.

Two more properties of the configuration, both from `logging_setup`:

- the three JSONL sinks set `propagate = False`, so high-volume SQL and HTTP
  records never reach the terminal or `console.log`. The terminal stays
  readable while the artefacts stay complete;
- colour is applied only when `sys.stdout.isatty()`, so a redirected run and
  a CI log contain no escape codes.

---

## 4. Run ids, and how to correlate

### 4.1 Format

`common.context.new_run_id()` returns `YYYYmmdd-HHMMSS-xxxx`, UTC timestamp
plus four hex characters. Timestamped so directories sort chronologically;
suffixed so two runs started in the same second do not collide.

### 4.2 One logical run across several processes

`init_run()` honours `SITING_ATLAS_RUN_ID` and exports it back into the
environment. Set it and several Python invocations share one log directory,
appending rather than overwriting:

```bash
export SITING_ATLAS_RUN_ID=doc-demo
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.normalise
PYTHONPATH=src .venv/bin/python -m siting_atlas.ingest.external --check
```

Both write into `logs/run-doc-demo/`. This is how a shell script that calls
four stages produces one auditable run rather than four unrelated ones.

### 4.3 Correlating to results

Every metric file written through `common.log_json.write_json` is stamped
with the run that produced it, so a number in `outputs/metrics/` names the
log directory that explains it:

```bash
jq -r '.run_id' experiments/superseded-artefacts/panel_report.json
```

Acquisition goes the other way too: each line of `data/raw/manifest.jsonl`
carries the `run_id` of the fetch, so a cached file can be traced to the
request that produced it.

---

## 5. The layer model

`common/context.py` defines the codes. They are the same L0-L5 used
throughout the documentation, plus a sentinel for anything that runs before
the pipeline proper.

| Code | Name | Reads | Writes |
|---|---|---|---|
| `L0` | acquire | the network | `data/raw/`, `data/external/` validation |
| `L1` | normalise | `data/raw/`, `data/external/` | `data/interim/*.parquet` |
| `L2` | warehouse | `data/interim/` | `data/processed/siting_atlas.duckdb` |
| `L3` | feature | the warehouse | `data/processed/panel.parquet` |
| `L4` | model | the panel | `outputs/metrics/` (and `outputs/models/`, declared at `common/paths.py:38` and never written) |
| `L5` | report | estimates | figures, tables, metrics |
| `--` | setup | — | bootstrap, config, anything pre-pipeline |

`context.layer()` raises `ValueError` on an unknown code, so a typo is caught
at the boundary instead of producing records tagged `unknown` that nobody
notices. All six layers are entered by real modules. Re-enumerated 2026-09-14
from `grep -rn "traced_layer(" src/`, because the previous list was
incomplete:

```
  L0  ingest/ acquire, probe, external, census_api, eia_api, osha, nlrb
  L1  ingest/ normalise, normalise_external, cbp_detail, osm_landuse
  L2  warehouse/schema.py
  L3  warehouse/panel.py
  L4  cost/runner.py, optimize/runner.py, optimize/montecarlo.py,
      models/runner.py, agent/runner.py, ingest/nlrb_capture.py
  L5  report/scope.py, viz/build.py, models/choice_runner.py
```

**Two of those are tagged wrong and neither document had recorded it.**
`ingest/nlrb_capture.py` is an ingest module entering L4, and
`models/choice_runner.py` — the project's current headline model — enters
**L5, the report layer**. It is the same layer-tag inconsistency `PIPELINE.md`
§2.5 flags for `census_api` and `eia_api`: the code raises on an unknown
layer, but nothing checks that a module is in the layer it belongs to, so the
tag is a convention and conventions drift.

A layer is entered through `trace.traced_layer`, which logs both sides of the
crossing:

```
01:42:53 I L2  trace                  => ENTER L2 (warehouse) - star schema...
01:42:56 I L2  trace                  <= LEAVE L2 (warehouse) in 3.23s
```

If the layer raises, the `LEAVE` becomes `ABORT` and the record carries the
exception type, message and full traceback. **A run that did not finish still
tells you how far it got**, which is the whole point of logging the crossing
rather than only the result.

Inside a layer, `trace.step(name)` names a unit of work and times it. Stage
names are conventionally `<verb>:<thing>` — `acquire:cbp_zip`,
`normalise:gazetteer`, `build:dim_county` — and that string is what appears
in the `stage` field of every record the step emits, including SQL and HTTP.

---

## 6. Debugging a failed run from the artefacts alone

Worked example, using a run that is still on disk:
`logs/run-20260912-063050-6920/`.

**Step 1 — find the run that went wrong.**

```bash
wc -l logs/run-*/errors.log | sort -rn | head -3
```

That run has 12 lines in `errors.log`; most others have none.

**Step 2 — read `errors.log` first, not `console.log`.** It is already
filtered to WARNING and above:

```
23:30:52 W L0  acquire:cbp_zip        attempt 1/3 failed (404 Client Error...
23:30:55 W L0  acquire:cbp_zip        attempt 2/3 failed (404 Client Error...
23:30:59 E L0  acquire:cbp_zip        giving up on https://www2.census.gov/...
23:30:59 E L0  acquire:cbp_zip        cbp_zip              FAIL  failed to ...
```

The stage column already names the source. Note the other ten lines are
`SKIP` warnings for sources needing a key or manual placement — expected
noise, and the reason `errors.log` is a triage tool rather than a verdict.

**Step 3 — get the full request from `http.jsonl`.** The console message is
truncated; the structured record is not:

```bash
jq -r 'select(.fields.error) | "\(.fields.attempt) \(.fields.error)"' \
    logs/run-20260912-063050-6920/http.jsonl
```

Three attempts, all `404 Client Error` for
`.../cbp/datasets/2023/zbp22totals.zip`. The diagnosis is in the URL: the
2022 reference-year file is filed under a `2022/` path, and a single global
vintage substitution had produced `2023/`.

**Step 4 — confirm the fix from a later run's artefacts.** `acquire.py` now
carries `VINTAGE_BY_SOURCE`, and the manifest records the successful fetch:

```bash
jq -r 'select(.source=="cbp_zip") | .url' data/raw/manifest.jsonl
```

returns the `2022/zbp22totals.zip` path.

### 6.1 Two traps in this workflow

**A handled failure is not a `step_fail`.** `ingest.acquire` catches
per-source exceptions so one dead endpoint does not abort the other eleven.
The step therefore closes as `step_ok` and
`jq 'select(.fields.event=="step_fail")'` returns nothing for this run. Look
in `errors.log` and in the `status` field of
`outputs/metrics/acquire_report.json`, not for `step_fail`.

**`errors.log` includes WARNING.** A non-empty `errors.log` does not mean the
run failed. Skips, retries and slow queries all land there by design.

---

## 7. Tracing one SQL statement back to its pipeline stage

Take a statement out of `sql.jsonl` and walk it back to the code.

**Step 1 — rank the statements a run executed.**

```bash
jq -r '.fields | "\(.seconds)\t\(.layer)\t\(.stage)\t\(.verb)"' \
    logs/run-20260912-084253-45ab/sql.jsonl | sort -rn | head -3
```

```
1.9205  L2      build:dim_date          CREATE
0.664   L2      build:fact_zcta_year    CREATE
0.2304  L2      build:dim_zcta          CREATE
```

**Step 2 — read the three context fields.** Every record carries them:

- `run_id` `20260912-084253-45ab` names the log directory;
- `layer` `L2` maps through `context.LAYERS` to `warehouse`;
- `stage` `build:dim_date` is the string passed to `trace.step`.

**Step 3 — grep the stage name in the source.** Stage names are literals, so
this always resolves:

```bash
grep -rn 'build:' src/siting_atlas/warehouse/schema.py
```

`schema.run()` iterates `BUILDERS` and opens `step(f"build:{name}")` around
each, so `build:dim_date` is `build_dim_date`. One grep, no guessing.

**Step 4 — get the statement itself.** The console preview is cut at 110
characters; `sql.jsonl` has the whole thing, whitespace collapsed to one
line, with its bound parameters:

```bash
jq -r '.fields | select(.stage=="build:dim_date") | .sql' \
    logs/run-20260912-084253-45ab/sql.jsonl | head -1
```

The reverse direction works too. `console.log` shows a statement's elapsed
time and stage inline, so a slow query spotted in the terminal already names
the stage to grep for.

---

## 8. What is redacted, and what is not

Five mechanisms, all in the source:

| Mechanism | Where | Covers |
|---|---|---|
| `http._redact` | `common/http.py:59` | query parameters named `key`, `api_key`, `token`, `apikey` (`_SECRET_PARAMS`, `:39`), in the logged URL and in the manifest |
| `http._scrub` | `common/http.py:81` | credentials in **arbitrary text**, including exception messages and `Authorization: Bearer`/`Basic` headers. Applied on every log path out of `fetch` (`:278`, `:284`, `:287`, `:290`). See §8.1 |
| `http._scrub_cached` | `common/http.py:114` | a credential the **server echoed back** into its own response body, before it is cached into `data/raw/` |
| `shell._safe_env` | `common/shell.py` | environment overrides whose name contains `KEY`, `TOKEN`, `SECRET`, `PASSWORD`, `PASSWD`, `CREDENTIAL` |
| `http.api_key` | `common/http.py` | logs only whether a variable was present, never its value |

`config.load_dotenv()` reads `.env` into the environment and logs nothing at
all. `.env` is gitignored.

### 8.1 The gap that was here — RESOLVED, both halves

This section reported two live problems. **Both are fixed in source, and both
fixes were verified against the tree on 2026-09-13.** The account is kept
rather than deleted, because the incident is the reason the fourth mechanism
exists and a reader who finds a stale key in an old log needs to know how it
got there.

**The defect, as it stood.** Redaction covered the URL the logger builds, not
the URL inside an exception message. When `requests` raises `HTTPError`, its
message contains the fully-expanded URL, query string included, so logging
the exception verbatim on the retry path wrote the live key into
`console.log`, `events.jsonl` and `errors.log` at once. It was observed with
a real `EIA_API_KEY`; the affected log directory was deleted rather than kept
as an example. The second, distinct vector: the EIA v2 API echoes
`request.params.api_key` back in its **response body**, which was being
cached verbatim into `data/raw/`.

**Fix 1 — the exception string is scrubbed.** `common/http.py:81` defines
`_scrub()`, and the retry path now reads:

```python
_log.warning("attempt %d/%d failed (%s); retry in %.0fs",
             attempt, RETRIES, _scrub(exc), wait)     # http.py:283-284
```

`_scrub` is also applied to the give-up message (`:287`) and to the
`RuntimeError` that is raised (`:290`), so no path out of `fetch` carries a
raw exception. (An earlier draft named `http.py:278` as "the `errors.log`
record". It is not: `:278` is the `_http_log.debug` record, `_http_log` has
`propagate = False`, and it reaches `http.jsonl` only. The records that do
reach `errors.log` are the WARNING at `:283` and the ERROR at `:287`, both
scrubbed.) It makes three passes,
because each alone leaks: a `name=value` regex over the secret parameter
names; an `Authorization: Bearer`/`Basic` regex, which has no `name=` for the
first pass to key off and arrives via `common/shell.py` in argv rather than
in a URL; and literal replacement of the current values of every variable in
`_SECRET_ENV_VARS`, which catches a bare key pasted into a message with no
`name=` around it. The literal pass is guarded at `len(val) >= 8` so that a
one-character value cannot blank the whole message, and all three are
idempotent because the replacement text contains `<` and `>`, which every
pattern excludes. The echoed-response vector has its own fix,
`_scrub_cached()` at `http.py:114`, which rewrites the cached file and
returns the corrected byte count and hash so the manifest describes what is
actually on disk.

**Fix 2 — `logs/` is gitignored.** `.gitignore:32`, under a comment written
out at `:29-31`: *"run logs are never committed. they record every URL, SQL
statement and shell command a run issued, so a single un-scrubbed line could
publish a credential. re-derivable by re-running; not worth the risk."*
`.env` and `*.key` are ignored at `:43-44`. `DECISION_LOG.md` §2.10 records
the sweep: all 415 log run-directories existing at the time, and the whole
tree, were searched for the current key, and it appears in **zero** files
outside `.env`. There are 592 run directories as of 2026-09-14, so a reader
re-running the check will see a larger denominator; the sweep is a record of a
past run, not a standing guarantee.

**The table in §8 above has been extended accordingly** — it listed three
mechanisms and now lists five, `_scrub` and `_scrub_cached` being the two it
was missing.

**What remains, correctly, as WIP.** A *new* keyed source added without
adding its variable to `_SECRET_ENV_VARS` (`http.py:44`) and its parameter
name to `_SECRET_PARAMS` (`:39`) would still leak. That residual is flagged
in `../ARCHITECTURE.md` §8. Note
those flags are slightly more pessimistic than the code: the literal-value
pass covers any variable once it is added to `_SECRET_ENV_VARS`, without
needing a new regex.

The check below still costs nothing and is worth running before sharing a log
directory from any run that failed against a keyed API:

```bash
grep -rl "$(grep EIA_API_KEY .env | cut -d= -f2)" logs/ 2>/dev/null
```

---

## 9. Adding logging to a new stage

The whole contract is four imports and two context managers.

```python
from ..common import paths
from ..common.context import init_run
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer

_log = get_logger("myfeature")


def main() -> int:
    paths.ensure_dirs()
    init_run()          # adopt SITING_ATLAS_RUN_ID, or mint one
    configure()         # install handlers; idempotent

    with traced_layer("L3", "what this layer is for"):
        with step("myfeature:thing"):
            out = do_work()
            artefact(out, rows=len(frame))
            metric("thing_rows", len(frame))
    return 0
```

Four rules that keep the artefacts worth reading:

1. **`init_run()` then `configure()`, once, in `main()`.** Never at import
   time in a stage module. `configure()` is idempotent, so a stage imported
   by another stage does not double-install handlers.
2. **Never open a DuckDB connection directly.** Use `common.db.connect()` or
   the statement never reaches `sql.jsonl`.
3. **Never call `subprocess` directly.** Use `common.shell.run()`.
4. **Record every file you write with `artefact()`.** A run should be
   auditable for what it produced without listing the filesystem.

---

## 10. Quick reference

```bash
# which runs went wrong
wc -l logs/run-*/errors.log | sort -rn | head

# what a run produced
jq -r '.fields | select(.event=="artefact") | "\(.rows)\t\(.path)"' \
    logs/run-<id>/events.jsonl

# every measured quantity
jq -r '.fields | select(.event=="metric") | "\(.name)\t\(.value)"' \
    logs/run-<id>/events.jsonl

# slowest statements, with the stage that ran them
jq -r '.fields | "\(.seconds)\t\(.stage)\t\(.verb)"' \
    logs/run-<id>/sql.jsonl | sort -rn | head

# downloads, cached or not
jq -r '.fields | "\(.cached)\t\(.source)\t\(.bytes)"' \
    logs/run-<id>/http.jsonl

# how long each layer took
jq -r 'select(.fields.event=="layer_leave")
       | "\(.layer)\t\(.fields.seconds)"' logs/run-<id>/events.jsonl
```

| Want | File |
|---|---|
| what a person would have seen | `console.log` |
| what went wrong | `errors.log` |
| what the run produced | `events.jsonl`, `event=artefact` |
| which query was slow | `sql.jsonl` |
| whether the network was hit | `http.jsonl`, `cached` |
| which external tool ran | `commands.jsonl` |
