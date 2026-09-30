# Week 5 of 12 — What the public record cannot see

> **Week 5 of 12.** The project is finished; these twelve pages pace how it is walked through, one week at a time. Nothing below is typed in. Every number is read out of the artefact named beside it at build time, and each artefact carries the real `run_id` and build date of the run that produced it, so the actual chronology is on the page.

| | |
|---|---|
| **Question** | Before modelling anything — how much of this network is visible in free public data at all? |
| **Run it** | `bash run_week.sh 05` |
| **Mode** | **INSPECT** — the command below reads what already ships and recomputes nothing, so the number is reported rather than demonstrated. Why not recomputed here: the intersection needs the OSHA enforcement extract from the L0 cache |
| **What runs** | reads the two-list coverage intersection |
| **Artefact** | `outputs/metrics/mwpvl_coverage.json` · run `20260916-071059-05ed` · built 2026-09-16 |

## What this stage does
OSHA enforcement data is the best free source of facility addresses in the
United States. Set its city list against an independent industry census of
delivery-station cities, and intersect.

This is a **two-list intersection, counted** — not a capture-recapture
estimate, and deliberately so. It is a FLOOR on the gap: MWPVL's side is
restricted to small-package delivery stations while OSHA's side is every
facility class, so the comparison is biased towards making the public
record look BETTER than it is. The real gap is at least this wide.

This week is the project's pivot. It is why the prediction question in week
7 was always going to be hard, and it is the finding that survived when the
prediction did not.

## What came back

| Measure | Value | Read from |
|---|---|---|
| Cities with a delivery station | **488** | `mwpvl_coverage.mwpvl_delivery_station_cities` |
| Of those, in OSHA records | **138** | `mwpvl_coverage.cities_in_both` |
| Never inspected | **350** | `mwpvl_coverage.cities_..._never_inspected` |
| Share OSHA has seen | **28.28%** | `mwpvl_coverage.share_of_mwpvl_cities_osha_has_seen` |

## What this week does *not* establish

- Cities, not buildings. This panel cannot say what share of individual facilities are unrecorded, only what share of the places holding them are.
- Matching is by a normalised city+state key, and 39 MWPVL rows have no usable city; they are excluded from both sides.

## Read next

- [`docs/NUMBERS.md`](../../../../siting-atlas/docs/NUMBERS.md) — the intersection re-derived, with the matching rule stated

---

[← Week 4](WEEK-04.md) · [Index](../README.md) · [Week 6 →](WEEK-06.md)
