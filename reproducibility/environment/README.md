# reproducibility/environment — the interpreter pin

One file, `python-version`, containing `3.11`.

Hand-written and tracked. It is the value `requires-python` in
`pyproject.toml` and the `python-version` in the CI matrix
(`.github/workflows/ci.yml`) both have to agree with; a single place to look
when a run behaves differently on two machines.

**Dependencies are not here.** They are pinned in `pyproject.toml` (with the
reason each one is present) and `requirements-lock.txt`. Seeds are in
[`../seeds.toml`](../seeds.toml). See [`../README.md`](../README.md) for what
else a re-run has to agree with and where it lives.
