# superseded-artefacts

Results computed on the **104-facility pilot panel**, before the OCR
extraction expanded it to 693. [`../README.md`](../README.md#superseded-artefacts)
explains why they are kept.

Four files, all moved out of `outputs/metrics/` on 2026-09-15:

```
  panel_report.json           the pilot ZCTA-quarter panel
  panel_report_national.json  the same panel, national facility frame
  national_panel.json         104 rows in national_facilities.csv
  external_check.json         schema/row checks on the hand-placed sources
```

They are **not wrong** — they are answers to the same questions asked of a
smaller sample. Where a current artefact exists it supersedes these; the
expanded counterparts are `panel_report_expanded.json` and
`national_panel_expanded.json` in [`../../outputs/metrics/`](../../outputs/metrics/).

Unlike the other four programmes here, these artefacts' emitters are still
live in `src/siting_atlas` (`warehouse.panel`, `warehouse.national`,
`ingest.external`), so there is no `code/` to archive here — every one of
these can be re-derived by re-running its stage against the pilot frame.
