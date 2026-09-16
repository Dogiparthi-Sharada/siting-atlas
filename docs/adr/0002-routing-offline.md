# ADR 0002 — Precompute drive times offline; ship no routing engine

- **Status:** accepted
- **Date:** 2026-09-08
- **Deciders:** P1 / P2

## Context

The cost model needs drive time from the nearest node to each ZCTA. The obvious
implementation runs OSRM against OpenStreetMap extracts.

OSRM preprocesses the road graph, and preprocessing scales badly: a metro
extract yields 2–5 GB of artifacts, a state extract 15–25 GB, and a full-US
extract needs 64–128 GB of RAM. Serving ten metros simultaneously means roughly
30 GB retained, and on 8 GB of RAM a large metro fails outright.

This was the single biggest infrastructure risk in the project.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| Live routing service for ten metros | Exact, queryable | ~30 GB; laptop-hostile; a demo dependency |
| **Offline per-metro precompute, delete artifacts** | Peak disk ~8 GB; no runtime dependency | Fixed node set; recompute if nodes change |
| Circuity approximation only | Trivial; no OSM at all | Loses road topology |

## Decision

Process one metro at a time, extract the origin–destination matrix, **delete
the extract and every artifact before the next metro.** Ship ten parquet files
totalling ~10 MB. The deployed application carries no routing dependency.

Retain the circuity approximation (road ≈ great-circle × 1.35, calibrated on one
metro against routed truth) as a documented fallback.

## Consequences

- Peak disk falls from ~60 GB to ~8 GB.
- No container, no cold start, and nothing routing-related that can fail live.
- Daganzo's law is already a continuous approximation, so exact routing was
  precision in the wrong place.
- Adding a candidate node requires re-running that metro's extraction.

## Residual risk

If the candidate node set changes substantially late in the project, the matrix
must be regenerated. Mitigated by generating over a generous candidate set up
front.

## Update — 2026-09-14: this decision was never implemented

**Everything above the line is a design. None of it was built.** The status
line stays as it is, because the decision was genuinely taken and is still the
right one; but an accepted ADR that reads in the past tense has been quoted
elsewhere in this repository as completed engineering work, and this section
exists to stop that.

What is actually true:

- **No OSRM was ever run**, on any metro. There is no OpenStreetMap extract, no
  preprocessing step and no routing code in `src/`.
- **No origin–destination matrix exists.** The "ten parquet files totalling
  ~10 MB" in the Decision section were never produced. There is no OD parquet
  anywhere in `outputs/`.
- **No disk figure in this ADR was ever measured.** The 2–5 GB per metro, the
  15–25 GB per state, the ~30 GB retained, the 64–128 GB of RAM, and the
  headline consequence "peak disk falls from ~60 GB to ~8 GB" are all
  *estimates made before the work*, not observations. Quote them as the
  reasoning that led to the decision. Do not quote them as a saving that was
  achieved, and do not put the 60 GB → 8 GB figure on a CV: it was billed that
  way in `../career/SCALE_AND_IMPACT.md` and has been removed from it.
- **The circuity approximation is not the fallback; it is the implementation.**
  What the Decision section calls "a documented fallback" is the only distance
  model the cost layer has ever had.
- **The circuity constant is wrong in the text above, twice over.** This ADR
  says "road ≈ great-circle × 1.35, calibrated on one metro against routed
  truth". The implemented value is **1.30**, visible in the parameter block of
  `../../outputs/metrics/cost_report.json`. And it cannot have been calibrated
  against routed truth, because no routing was ever run and therefore no routed
  truth exists. 1.3 is a literature default adopted without local calibration,
  and it should be described that way.

The consequence that *is* real is the one about the shipped artefact: the
application carries no routing dependency, no container and no cold start.
That was achieved — by not building the thing at all rather than by
precomputing it, which is a weaker claim than the one this ADR makes.

Whoever revisits this should decide explicitly between implementing the OD
matrix and superseding this ADR with one that adopts circuity on purpose. Until
then the project has an accepted decision and an unrelated implementation.
