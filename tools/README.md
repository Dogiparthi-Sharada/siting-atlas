# tools/ — the document build

Everything here produces a **document**, not a result. Nothing in this tree is
part of the analytical pipeline, nothing here reads `data/`, and nothing here
is imported by `src/siting_atlas`. That separation is deliberate: a slide deck
must never be able to change a number.

`bash scripts/build_all.sh` (or `make docs`) runs them in the order that
matters — figures, then the proposal, then the decks with a layout check on
each. (There used to be a fourth stage rendering a `.txt` twin of every
Markdown file. The twins and their generator were deleted on 2026-09-16; the
script says why, and it should not be added back.)

Each directory below has its own README with the exact commands.

## Directories

```
  figures/    the illustration PNGs in docs/figures/.
              build_all.py is the entry point; fig_*.py is one module per
              figure; common.py holds the shared style and the glyph
              measurement. Output: docs/figures/*.png
  proposal/   the proposal .docx. build_v4.py and build_v5.py are the entry
              points; docx_kit.py is the rendering layer; sections_*.py are
              the content, split by part
  deck/       the .pptx decks. build_deck.py is the entry point; pptx_kit.py
              and textfit.py are the rendering layer; slides_*.py are the
              content; check_layout.py verifies the result afterwards using
              the same measurement code that produced it
  paper/      the IEEE paper's .docx. build_docx.py converts
              paper/siting_atlas_ieee.tex, which is the source of truth;
              ieee_style.py is the styling and tex_blocks.py the parser.
              NOT part of build_all.sh -- run it by hand
  docs/       one utility. gen_data_docs.py regenerates docs/data/README.md
              and docs/data/<source>.md from the source registry in
              src/siting_atlas/ingest/sources.py
  ocr/        not a document builder. The OCR pass that recovered the MWPVL
              facility table; it has its own README
```

Two loose scripts sit at this level: `hazard_metrics.py` and `scope.py`.

## Two things worth knowing

**Text cannot overflow a box, by construction.** Both the figure toolkit and
the slide toolkit measure rendered glyph extents and shrink until the text
fits; `deck/check_layout.py` then verifies it independently. The first
validated run caught 21 defects that visual review had missed.

**`gen_data_docs.py` overwrites hand edits.** `docs/data/README.md` is
generated, and it currently carries a hand-corrected sentence about the
drive-time matrix. The next run of the generator will restore the false
version unless `ingest/registry.py:303` and `gen_data_docs.py:172` are fixed
first. The file says so at the top.

`tools/` is excluded from the merge-gate ruff config. Lint it explicitly with
`make lint-tools`.
