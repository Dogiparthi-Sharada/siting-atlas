# collection/keys — ANSWER KEYS. Not credentials.

**Nothing in this folder is a secret.** These are four CSVs of known answers
used to mark the model's work. The directory name is unfortunate and is kept
only because these filenames appear in the provenance document and the audit
trail. There is no key material anywhere in this repository.

Part of the labelling effort described in [`../README.md`](../README.md).

```
  OSHA_CLASSIFY_KEY.csv    83 rows   n,address,city,state,zip,operating_by
  NATIONAL_KEY.csv        320 rows
  GEMINI_KEY.csv           36 rows
  OSHA_ROUND2_KEY.csv      30 rows
```

Each key pairs an address with something the model was never told — usually
`operating_by`, an OSHA inspection date proving the building was already
operating by then. A claimed opening date later than that is **falsified**,
not merely doubtful. That check is edit `E_operating_by`, and it is the same
rule later used to validate the OCR extraction.
