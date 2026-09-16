# tools/proposal

Covered by [`../README.md`](../README.md) — read that first.

Builds the proposal `.docx` into `docs/proposal/` (the builders create the
directory; it is not in the repository until something writes there).

```bash
python tools/figures/build_all.py          # figures first - they are embedded
python tools/proposal/build_v5.py          # the current deliverable
python tools/proposal/build_v4.py          # the superseded v4, by hand only
```

`docx_kit.py` is the rendering layer; `sections_*.py` is v4's content, split by
part. **The two builders differ in where the prose lives:** v4 assembles it
from those Python modules, v5 renders `docs/proposal/PROPOSAL_V5.md` so the
Markdown and the Word file cannot drift. `scripts/build_all.sh` runs v5 only —
v4 is historical and is deliberately not rebuilt.

**Neither builds in a fresh clone today.** v5's source
(`docs/proposal/PROPOSAL_V5.md`) is not in the tree, and v4's
`REQUIRED_FIGURES` names `fig10`–`fig14`, which `docs/figures/` does not
currently hold. Both fail loudly rather than emitting a document with a hole
in it; see `docs/figures/README.md`.
