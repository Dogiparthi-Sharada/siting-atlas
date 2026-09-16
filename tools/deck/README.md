# tools/deck

Covered by [`../README.md`](../README.md) — read that first.

Builds the two `.pptx` decks into `docs/proposal/`, then validates them.

```bash
python tools/figures/build_all.py          # figures first - they are embedded
python tools/deck/build_deck.py            # both variants
python tools/deck/build_deck.py --variant v1   # v1 overview only (26 slides)
python tools/deck/check_layout.py docs/proposal/Siting_Atlas_Deck_v1_overview.pptx
```

**`build_deck.py` does not run in this tree today** — it imports the figure
modules and inherits their missing-`hazard_report.json` failure. See
[`../figures/README.md`](../figures/README.md).

`build_deck.py` is the entry point; `pptx_kit.py` and `textfit.py` are the
rendering layer; `slides_*.py` are the content and `notes_v1.py`/`notes_v2.py`
the presenter notes. `check_layout.py` re-measures the finished file against
three geometric rules and exits 1 on a violation — it is the independent
check, so run it even when the build looks fine. `bash scripts/build_all.sh`
does all of this in order.
