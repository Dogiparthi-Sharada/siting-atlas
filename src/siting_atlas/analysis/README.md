# analysis/ — questions the target variable cannot answer

Everything in `models/` answers *"where did Amazon build?"* and is therefore
capped by what the facility panel saw. This package asks the complementary
question — **where did Amazon not build, and does that predict anything?** —
which needs coverage geometry rather than a fitted model.

```bash
PYTHONPATH=src python -m siting_atlas.analysis.white_space
```

Output: `outputs/metrics/white_space.json`. The artefact carries no `run_id`;
only its file mtime backs it.

## Modules

```
  white_space.py           the entry point and the analysis
  white_space_network.py   the facility network a coverage map is drawn from,
                           and what it costs. Three sources joined here and
                           nowhere else
  white_space_cover.py     coverage as a union of discs, and the ranked list
                           of what falls outside. Deliberately the simplest
                           geometry that can be checked by hand
  white_space_backtest.py  hold out 2024-25 and ask whether the white space
                           predicted it. A coverage map is unfalsifiable on
                           its own -- it describes the present
  white_space_rules.py     the horse-race that isolates WHY the backtest
                           failed
  white_space_diagnose.py  reading that horse-race: which explanation the
                           numbers support
  white_space_print.py     the console tables. Computes nothing
```

## The result, and it is negative

White space **does not beat a household baseline**. It wins 14 of 108 scored
cells (13%), with **0 significant wins against 32 for the baseline** under a
two-sided exact McNemar test on discordant openings. The diagnosis is in the
artefact's own `why_it_failed` block: the defect is the *mask* — excluding
already-served places — not the idea and not the blob artefact.

**What the analysis did produce, and it is worth keeping.** A densification
measurement. At the headline 45-mile radius, **68.7%–75.9%** of 2024–25
delivery-station openings land inside pre-2024 coverage: 75.9% (60 of 79) on
real coordinates, 68.7% (90 of 131) with a ZCTA-centroid fallback. That range
is **across coordinate sets at one radius, not across radii** — 67.1% is the
real-coordinates 15-mile figure, and quoting "67–77%" mixes the two axes.

The artefact also carries a `falsification` clause: if Amazon opens a
delivery station in a place flagged here, that is a hit, and it is recorded in
advance. Notes:
[`docs/research/NOTES_WHITE_SPACE.md`](../../../docs/research/NOTES_WHITE_SPACE.md).

**No module in this package is reachable from any test.** All seven are in
the 78-of-181 list in [`docs/NUMBERS.md`](../../../docs/NUMBERS.md) §12.
