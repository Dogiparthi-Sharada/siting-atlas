# tools/figures

Covered by [`../README.md`](../README.md) — read that first for how this fits
into the document build.

Builds the illustration PNGs in `docs/figures/`: `build_all.py` is the entry
point, `fig_*.py` is one module per figure, `common.py`/`figbase.py` hold the
shared style and the glyph measurement that makes overflow impossible.

```bash
python tools/figures/build_all.py [--out docs/figures]
```

**`build_all.py` does not run in this tree today.** It imports `fig_backtest`,
which imports `tools/hazard_metrics.py`, which reads
`outputs/metrics/hazard_report.json` — a file that moved to
`experiments/hazard-model/artefacts/` when the hazard model was retired on
2026-09-15. The failure is a clear `FileNotFoundError` at import, and it takes
`tools/deck/build_deck.py` and the CI `documents` job down with it. Fixing the
path in `tools/hazard_metrics.py:32` is the whole repair.

`fig_hero_cost.py` (the README's hero chart) and `fig_paper.py` (the paper's
four result figures) are separate entry points, not part of `build_all.py`'s
numbered `fig01`–`fig14` set. `docs/figures/README.md` indexes all three
builders' output and says which figures carry measured numbers.
