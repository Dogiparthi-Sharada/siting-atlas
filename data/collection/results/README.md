# collection/results — what came back

Part of the labelling effort described in [`../README.md`](../README.md) — the
output side of the prompts in [`../prompts/`](../prompts/).

```
  NATIONAL_CLASSIFIED.csv             320 rows, the five national batches
  OSHA_CLASSIFIED.csv                  83 rows, the OSHA pass
  UNLABELLED_BATCH_<n>_CLASSIFIED.csv  six files, the parsed answers
  UNLABELLED_BATCH_<n>_RAW.txt         six files, the model's reply before
                                       parsing -- kept so a parsing error can
                                       be told apart from a model error
  DS_PANEL.csv                         the delivery stations that survived
  BATCH_DS_CANDIDATES.csv              candidates carried forward for review
  DATES_FOUND.csv                      the date pass (see ../dates/)
```

**A row here is a proposal, not a fact.** Every one was checked against
[`../keys/`](../keys/) before anything reached the facility panel, and a row
that survives the check is *not falsified* rather than proven correct. The
asymmetry is explained in the parent README.
