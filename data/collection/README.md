# How we worked out which buildings are delivery stations

This directory is the **provenance of the target variable**. Every prompt,
worklist, answer key and result from the human-in-the-loop labelling is kept
here, unedited, so that the single most important judgement in the project —
*is this building a delivery station or something else?* — can be audited by
someone who was not there.

It is 47 tracked files, about 407 KB. It ships with the repository on purpose.

---

## The problem

OSHA publishes inspection records for Amazon buildings. It does **not** say
what kind of building each one is. An Amazon site might be:

```
  delivery station      what we want -- last-mile, vans, 100-250k sq ft
  fulfilment centre     much larger, different economics, wrong unit
  sortation centre      middle of the network, not last-mile
  air hub / Prime Air   wrong class entirely
  Whole Foods / AFC     retail, not logistics
  closed                was one, no longer
```

Mixing those produces a panel that answers no question. A fulfilment centre
and a delivery station are not two draws from one distribution — they are
different decisions, made by different teams, against different constraints.
**Class purity is a precondition, not a nicety.**

## What we did

Six collection methods were attempted and five failed before one worked:
four before the labelling programme, plus the satellite route below. They are all recorded
in [`../../docs/data/FACILITY_PANEL_PROVENANCE.md`](../../docs/data/FACILITY_PANEL_PROVENANCE.md);
this directory holds the one that produced usable labels.

The method: **batch the unlabelled addresses, ask a language model to classify
and date each one with a source URL, then verify the answers against evidence
the model did not supply.**

```
  prompts/     what was asked, verbatim
  results/     what came back, parsed to CSV
  keys/        the ANSWER KEYS used to check the answers
  dates/       the separate date-lookup pass and its prompt
  satellite/   a sixth method that failed; kept as a negative result
```

### The prompts

[`prompts/GEMINI_PROMPT.txt`](prompts/GEMINI_PROMPT.txt) is representative. The
parts that matter are the constraints, not the question:

```
  - If you cannot find a real dated source, write UNKNOWN. Do not estimate.
  - Give a working source URL for every date.
  - Write "announced" instead of "opened" if the source only says Amazon
    planned or proposed the site.
  - If a location is actually a fulfillment centre or sortation centre
    rather than a delivery station, say so.
  - If it has closed, say so and give the closing year.
```

**"Do not estimate" and "give a working source URL" are the whole design.** A
model asked to classify will always produce a class; the only way to get a
usable label is to make *refusing* an allowed answer and to require evidence
that can be checked. `UNKNOWN` was a frequent and welcome response.

Six batches of unlabelled addresses (`UNLABELLED_BATCH_1..6.txt`), five
national batches, and one OSHA classification pass
(`OSHA_TO_CLASSIFY.txt`) were run this way.

### The answer keys

**`keys/` contains answer keys, not credentials.** Nothing in this directory
is a secret; the naming is unfortunate and is kept only because the filenames
appear in the provenance document and in the audit trail.

Each key pairs an address with something the model was not told — most often
`operating_by`, an OSHA inspection date proving the building was already
operating by then. A claimed opening date later than that is **falsified**,
not merely doubtful. That edit is `E_operating_by`, and it is the same rule
used later to validate the OCR extraction, where it gives a 94.71% pass rate.

```
  keys/OSHA_CLASSIFY_KEY.csv     82 rows   n,address,city,state,zip,operating_by
  keys/NATIONAL_KEY.csv         319 rows
  keys/GEMINI_KEY.csv            35 rows
  keys/OSHA_ROUND2_KEY.csv       29 rows
```

### What came out

```
  results/NATIONAL_CLASSIFIED.csv          319 rows
  results/OSHA_CLASSIFIED.csv               82 rows
  results/UNLABELLED_BATCH_*_CLASSIFIED.csv  6 files
  results/DS_PANEL.csv                      the surviving delivery stations
  results/DATES_FOUND.csv                   the date pass
```

## What this method is, honestly

It is **LLM-assisted labelling with external verification**, and it should be
described that way rather than as either "we classified them" or "the model
classified them". Specifically:

- The model proposes a class and a date **with a source URL**.
- The proposal is checked against an independent record (OSHA inspection
  dates) that the model never saw.
- Anything falsified by that check is dropped, not corrected.
- `UNKNOWN` is an accepted answer and was returned often.

**The limitation is real and is not hidden.** A label that survives the check
is not proven correct — it is only *not falsified*. The check has one
direction: it can prove a building was operating earlier than claimed, and it
can never prove an opening date is right. An unchecked row is not a passing
row. That asymmetry is why the facility panel carries an *upper bound* on
every opening date and no lower bound, and why the satellite programme below
was attempted at all.

## The sixth method, which failed

[`satellite/colab_date_from_satellite.py`](satellite/colab_date_from_satellite.py)
is a standalone Google Colab notebook — no API key, no Earth Engine account,
no payment — that tries to date construction from free Sentinel-2 imagery. A
delivery station is a large bright roof appearing where bare ground was, and
10-metre pixels every five days back to 2015 should see that.

It produced an estimate for **107 of 107** sites and then failed the
`E_operating_by` check on **36%** of them: 39 estimates date construction
*after* an inspector had already found the building operating, a median of 33
months after.

It is kept, and it runs, because the contrast is the point. A method that
answers every question is not thereby a good method — **the 94.71% pass rate
of the OCR extraction only means something because this comparison exists.**

## Related

- [`../../docs/data/FACILITY_PANEL_PROVENANCE.md`](../../docs/data/FACILITY_PANEL_PROVENANCE.md)
  — the full account, including the four methods that failed before this one
  and the airport-code trap
- [`../../docs/data/SATELLITE.md`](../../docs/data/SATELLITE.md) — the
  satellite programme written up as a negative result
- [`../../tools/ocr/README.md`](../../tools/ocr/README.md) — the OCR pass that
  later expanded the panel from 104 to 693 rows
