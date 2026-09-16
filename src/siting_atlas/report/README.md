# report — the numbers the documents quote

L5. Two files. This package exists so that a figure printed in the
proposal, the deck or a slide is DERIVED from the same artefacts the model
reads, rather than typed once and left to drift.

**Start here:** `scope.py`. It is the whole package.

---

## Files

```
  file          purpose                                          state
  ------------  -----------------------------------------------  ------
  __init__.py   one-line package docstring                       current
  scope.py      measures the study's scope - ZCTAs, metros,      works
                coverage - and writes it to
                outputs/metrics/scope.json for the documents
                to read
```

## Why it exists

The proposal claimed "approximately 5,200 ZCTAs" in the ten pilot metros.
The measured figure against the official OMB delineation is 2,413. Nobody
lied: the number was estimated early, typed into nine places across the
proposal, the deck and four figures, and never checked against data again.
That is the failure mode this project is supposed to be about, so the scope
figures are now computed once and read everywhere.

## Running it

```
  python -m siting_atlas.report.scope
```

or `make scope`. Takes no arguments.

Writes `outputs/metrics/scope.json`. GENERATED — hand edits are lost, and
worse, a hand edit here silently changes a number in the proposal.

Nothing here is stale as far as this reading found.
