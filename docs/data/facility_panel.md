# Logistics facility panel with opening dates

**Registry key:** `facility_panel`  ·  **Status:** MANUAL

> No stable machine-readable endpoint. The file is placed by hand.

## At a glance

| | |
|---|---|
| Provider | Public facility inventories, filings and local press |
| Grain | `facility` |
| Role in the model | THE TARGET VARIABLE — service enablement and timing |
| Update cadence | continuous |
| Reporting lag | 1 months |
| Licence | Compiled from public sources; verify each compiler's terms |
| Credential | none |


## Endpoint

No stable endpoint. See the acquisition note below.

## Measured reachability

Probed **2026-09-12** from the build environment.

| | |
|---|---|
| Verdict | `manual` |
| HTTP status | n/a |
| Content-Type | `n/a` |
| Round trip | Nones |
| Detail | no stable endpoint; file placed by hand |

Re-measure with `python -m siting_atlas.ingest.probe`. The probe compares the live result against the declared status and warns on drift.

## Notes

No single stable endpoint. Compiled from published inventories, corporate announcements and permit records, and delivered as a 43-row CENSUS of what the sources actually yield rather than a sample - hand-verifying 100 is impossible on 43. Accuracy is instead evidenced by an external cross-check: five addresses appear in both MWPVL's 2012 table and the OSHA extract, the operating-by bound held 5 of 5, and the lag to first inspection ran 4 to 345 months. measured error rate reported. Terms of use of any third-party compilation must be checked before use.

## Acquisition procedure

1. Open the provider site in a browser.
2. Download the file described above.
3. Place it in `data/external/facility_panel/` keeping the original filename.
4. Record the download date and the source URL in `data/raw/manifest.jsonl` so provenance stays complete.

The pipeline treats a missing manual source as a skipped stage with a stated reason, not as a failure — the rest of the run still executes.

---

*Generated from `src/siting_atlas/ingest/sources.py`. Do not edit by hand — run `python tools/docs/gen_data_docs.py`.*
