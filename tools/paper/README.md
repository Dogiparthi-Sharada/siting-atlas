# tools/paper — the IEEE paper's Word converter

Not listed in [`../README.md`](../README.md), but it belongs to the same
document build: nothing here reads `data/`, nothing here is imported by
`src/siting_atlas`, and nothing here can change a number.

```bash
python tools/paper/build_docx.py
```

Reads `paper/siting_atlas_ieee.tex` and writes `paper/siting_atlas_ieee.docx`.
**The `.tex` is the source of truth** — this script converts it rather than
holding a second copy of the prose, which is the whole reason it exists
instead of a hand-written Word file. Figures are resolved by basename against
`docs/figures/` first, then `outputs/figures/`.

`ieee_style.py` holds the two-column IEEE styling; `tex_blocks.py` is the
`.tex` parser. Exit codes: 0 written, 2 source missing, 3 conversion failed.

This builder is **not** part of `scripts/build_all.sh` or `make docs`; run it
by hand after editing the `.tex`. See [`../../paper/README.md`](../../paper/README.md)
for the paper's status — draft, not submitted, not reviewed.
