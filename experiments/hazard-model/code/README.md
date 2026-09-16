# hazard-model/code

Archived. The question this programme asked and why it was retired are in
[`../../README.md`](../../README.md#hazard-model); do not duplicate it here.

What is in this folder: the discrete-time hazard stage as it stood when it was
removed from `src/` — `hazard.py` and `runner.py` (the original fit),
`sensitivities.py`, `catchment_band.py` (the radius sweep that still owns
`outputs/metrics/catchment_band.json`, which now has no live emitter), and the
five `hazard_revival_*.py` modules that refit it on 6.7x the events.

Imports point at `siting_atlas.*` paths that have since moved. Expect to fix
them before anything runs; the artefacts are the reliable record.
