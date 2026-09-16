# percapita-logrel/code

Archived. What the two reframings were and why neither survived is in
[`../../README.md`](../../README.md#percapita-logrel); not repeated here.

What is in this folder: `percapita_*.py`, the per-household rate arms
(`percapita_search.py` is the entry point), and `logrel_*.py`, the
log-relative arms (`logrel_search.py` is the entry point, `logrel_runner.py`
owns the resume checkpoint).

**The log-relative code no longer runs against current `src/`.** The
positivity guard in `models/choice.py` — which this experiment is the reason
for — raises on five of its ten arms. That is the guard working, not a
regression.
