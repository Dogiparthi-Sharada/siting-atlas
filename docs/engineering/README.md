# Engineering docs — index

*Index rewritten 2026-09-14, against a full re-check of all three documents
and of `src/`. The previous version was an errata sheet, and most of the
errata it listed had already been fixed — which made it the most misleading
file in the folder. Everything it flagged is accounted for below, under
either "still open" or "closed".*

Three documents about how the thing is built and run: what the pipeline
actually does today, what a run leaves behind in `logs/`, and the sizing and
architecture reasoning from before any of it was built.

---

## What is in this folder

Each `.md` has a generated `.txt` twin; the twins are not listed separately.
Line counts are deliberately omitted — they drifted three times in two days
and told a reader nothing.

```
  PIPELINE.md          CURRENT.  State dated 2026-09-13, every count
                       re-measured 2026-09-14.
    The as-built ledger. Every stage L0 to L5, the literal command that runs
    it, what it reads and writes, the row counts it actually produced. The
    author ran the whole pipeline in order while writing it. Ends with §9, a
    table of where the build diverges from the design documents.
    It knows the hazard model failed, and since 2026-09-13 it also carries
    the diagnosis (§6.3, the unit-of-analysis error) and points at the
    successor.

  LOGGING.md           CURRENT.  Checked against source 2026-09-12,
                       §8.1 re-checked 2026-09-13, §2.4/§5/§8 2026-09-14.
    The observability manual. The six files a run drops in logs/run-<id>/,
    the JSON shape and event vocabulary of each, log levels and
    SITING_ATLAS_LOG_LEVEL, how to correlate a run id across files, and
    worked jq/grep recipes for diagnosing a failed run from its artefacts
    without re-running it. Example lines are copied from real runs.
    Method-agnostic: the words "hazard", "cloglog" and "survival" do not
    appear once, so nothing in it changes when the model changes. The
    soundest of the three.

  DATA_ENGINEERING.md  PRE-BUILD REASONING.  Read last, and read the
                       correction notes, which are frequent.
    The sizing and feasibility brief written before the build: why this is
    deliberately not big data, the two things that could sink it on a student
    laptop, an L0-L4 reference architecture with owners, a hardware section,
    ten rules, and a risk register. Valuable as reasoning about trade-offs.
    Unreliable as description, because most of it describes a system that was
    then built differently. Its projections are now marked against measured
    values in place; several were wrong by an order of magnitude and one
    section (§2, routing) describes work that was never started at all.
```

---

## Start here

```
  1  PIPELINE.md          — what is actually true today, with a date on it
  2  LOGGING.md           — independent of the model debate; read it whenever
  3  DATA_ENGINEERING.md  — last, and only for the reasoning
```

Read `../STATUS.md` before or alongside `PIPELINE.md`; PIPELINE defers to it
and does not repeat the model diagnosis.

---

## What is still open

### DATA_ENGINEERING.md §2 describes a routing pipeline that was never built

There is no origin-destination matrix, no OSRM artefact, and no
`cost/od_matrix.py`. `grep -rli osrm src/` finds one docstring in
`common/shell.py`. The *decision* in `../adr/0002-routing-offline.md` is sound
and stands; the *execution* never happened, and the cost model uses
great-circle distance times a circuity factor of 1.30 instead.

§10 of that document now says so plainly, and §9's recommendation-1 — which
told the proposal to say *"OSRM is used once, offline, to precompute a
drive-time matrix"* — has been struck. **If you find any other sentence in
this repository written in that completed tense, it is wrong.** One is still
live outside this folder: `docs/data/README.md` carries it, emitted by
`tools/docs/gen_data_docs.py:172` and declared at
`src/siting_atlas/ingest/registry.py:303`, so fixing the generated file alone
will not hold.

### Data contracts are reported, not enforced

`PIPELINE.md` §9. One exception has been added since: `warehouse/flag_gate.py`
raises if a computed quality flag does not reach the panel. Everything else —
row-count drops, ZCTA count changes, unexpected nulls — is logged and the
build continues. Only the facility-panel check exits non-zero.

### The layer tags are a convention and nothing checks them

`models/choice_runner.py`, the current headline model, enters **L5**, the
report layer. `ingest/nlrb_capture.py`, an ingest module, enters **L4**.
`context.layer()` raises on an unknown *code*; nothing asserts that a module
is in the layer it belongs to. `LOGGING.md` §5 and `PIPELINE.md` §9 both now
record this.

### `outputs/models/` is declared and never written

`common/paths.py:38` declares it and `LOGGING.md` §5 names it as an L4 write
target. It is empty and `grep -rn "paths.MODELS" src/` finds only the
declaration. Either something should write it or it should go.

### Two ingest modules bypass the source registry

`ingest/cbp_detail.py` and `ingest/osm_landuse.py` read files that are not in
`ingest/sources.py` and not in `data/raw/manifest.jsonl`, so they have no
recorded hash, URL or fetch time. That breaks the provenance rule the project
states in `../data/README.md`. Both are documented by hand instead:
[`../data/CBP_DETAIL.md`](../data/CBP_DETAIL.md) and
[`../data/OSM_LANDUSE.md`](../data/OSM_LANDUSE.md).

---

## What is closed

Recorded rather than deleted, because the previous version of this index sent
readers to re-fix all of these and that is exactly the failure mode
`PIPELINE.md` §9 warns about.

```
  LOGGING.md sec.8.1 reported two live security defects
      CLOSED before 2026-09-13. The retry warning is scrubbed
      (http.py:283-284 shows _scrub(exc)); logs/ is gitignored at
      .gitignore:32; the sec.8 mechanism table lists five mechanisms
      including http._scrub and http._scrub_cached. The section is headed
      "RESOLVED, both halves".

  DATA_ENGINEERING.md describes unbuilt work in the completed past tense
      CLOSED for sec.2 and sec.10. The "we removed it from the critical
      path by precomputing the drive-time matrix" sentence no longer
      exists in the file; sec.2 opens with "Status, 2026-09-13: designed,
      not built". The sec.9 instance was struck on 2026-09-14 and is the
      last one in this folder.

  PIPELINE.md has no diagnosis or successor for the model failure
      CLOSED. PIPELINE.md sec.6.3 now states "The cause is the unit of
      analysis, not the sample size", explains the 812-from-104 collapse,
      and links ../METHODS_RESEARCH.md sec.14.2 and
      ../adr/0004-model-change-conditional-choice.md.

  All three are silent on the 104-station national panel
      CLOSED 2026-09-14. PIPELINE.md sec.7 now opens with both files.
      national_facilities.csv holds 104 rows describing 100 distinct
      buildings (experiments/superseded-artefacts/national_panel.json); 100 rows survive the
      E_operating_by edit at load and 94 become fitted decisions. See
      ../STATUS.md for the current reading.

  dbt/ is an empty skeleton
      SUPERSEDED. The directory has been DELETED, not emptied. L2 is
      warehouse/schema.py running DuckDB in process.

  Yelp versus CBP is an open decision
      CLOSED by ../adr/0003-public-sources-only.md. Yelp appears nowhere in
      src/. DATA_ENGINEERING.md sec.3 is marked as a record of a decision.
```

---

## The .txt twins

Every `.md` in the repo is rendered to a plain-ASCII `.txt` of the same name
by `scripts/build_docs.sh`. **The `.txt` files are generated — hand edits are
lost.** Edit the `.md` and re-run:

```
  bash scripts/build_docs.sh
```

Prose is **not** hard-wrapped: `WIDTH` defaults to 0, so each paragraph is one
long line for the reader's editor to soft-wrap. Tables, rules and heading
banners use a fixed 100-column geometry regardless, because their meaning is
in their alignment. `WIDTH=100 bash scripts/build_docs.sh` restores the old
fixed-width behaviour. To render a single file:

```
  .venv/bin/python tools/docs/md_to_txt.py IN.md OUT.txt
```
