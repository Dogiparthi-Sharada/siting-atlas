# EJScreen environmental justice indicators

**Registry key:** `ejscreen`  ·  **Status:** MANUAL

> No stable machine-readable endpoint. The file is placed by hand.

## At a glance

| | |
|---|---|
| Provider | US Environmental Protection Agency |
| Grain | `block_group` |
| Role in the model | Equity overlay — predicted burden by demographic stratum |
| Update cadence | annual |
| Reporting lag | 12 months |
| Licence | US Government Work (public domain) |
| Credential | none |

Provider documentation:

```
https://www.epa.gov/ejscreen
```

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

The historical gaftp.epa.gov paths now return 404; the distribution location has moved. Resolve the current URL from the landing page and place the file in data/external/.

## Acquisition procedure

1. Open https://www.epa.gov/ejscreen in a browser.
2. Download the file described above.
3. Place it in `data/external/ejscreen/` keeping the original filename.
4. Record the download date and the source URL in `data/raw/manifest.jsonl` so provenance stays complete.

The pipeline treats a missing manual source as a skipped stage with a stated reason, not as a failure — the rest of the run still executes.

---

*Generated from `src/siting_atlas/ingest/sources.py`. Do not edit by hand — run `python tools/docs/gen_data_docs.py`.*
