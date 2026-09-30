# Week 6 of 12 — What the public record cannot see  ◆ MIDTERM

> **Week 6 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | Before modelling anything: how much of this network is visible in free public data at all? |
| **Run it** | `bash run_week.sh 06` |
| **Mode** | **INSPECT** — the command below reads what already ships and recomputes nothing, so the number is reported rather than demonstrated. Why not recomputed here: the intersection needs the OSHA enforcement extract from the L0 cache |
| **What runs** | reads the two-list coverage intersection |
| **Artefact** | `outputs/metrics/mwpvl_coverage.json` · run `20260916-071059-05ed` · built 2026-09-16 |

> **Where we got to.** 138 of 488 cities. This is the project's actual finding, and it arrived in the middle of the semester and changed what the rest of it was for.

## What this stage does
OSHA enforcement data is the best free source of facility addresses in the
United States. Set its city list against an independent industry census of
delivery-station cities, and intersect them.

This is a **two-list intersection, counted** — not a capture-recapture
estimate, and deliberately so. It is a FLOOR on the gap: MWPVL's side is
restricted to small-package delivery stations while OSHA's side spans every
facility class, so the comparison is biased towards making the public record
look *better* than it is. The real gap is at least this wide.

**Why this is the turn of the project.** We came in intending to predict
where the next facility opens. This week said the public record cannot see
roughly three in four of the places that already have one. That does not
make prediction impossible, but it makes failure the likely outcome — and it
turns "our model lost" from an embarrassment into a measurement of something
real, *provided* we commit to the test in advance. Which is week 7.

## What came back

| Measure | Value | Read from |
|---|---|---|
| Cities with a delivery station | **488** | `mwpvl_coverage.mwpvl_delivery_station_cities` |
| Of those, in OSHA records | **138** | `mwpvl_coverage.cities_in_both` |
| Never inspected | **350** | `mwpvl_coverage.cities_..._never_inspected` |
| Share OSHA has seen | **28.28%** | `mwpvl_coverage.share_of_mwpvl_cities_osha_has_seen` |

## The risk we flagged

This is the week we learned the prediction question might be unanswerable. Raising it at the midterm rather than in week 11 is what made weeks 7-10 a designed response instead of a scramble.

## What this week does *not* establish

- Cities, not buildings. This panel cannot say what share of individual facilities are unrecorded, only what share of the places holding them are.
- Matching is by a normalised city and state key, and 39 rows have no usable city; they are excluded from both sides.

## Read next

- [`docs/NUMBERS.md`](../../../../siting-atlas/docs/NUMBERS.md) — the intersection re-derived, with the matching rule stated
- [`docs/DECISION_LOG.md`](../../../../siting-atlas/docs/DECISION_LOG.md) — the decision to keep going, and on what basis

---

[← Week 5](WEEK-05.md) · [Index](../README.md) · [Week 7 →](WEEK-07.md)
