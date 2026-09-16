# reproducibility — the two things a re-run has to agree with

Small on purpose. Two files: the random seeds, and the Python version.
Everything else that makes a run reproducible lives elsewhere —
`data/raw/manifest.jsonl` for the inputs, `pyproject.toml` for the
dependencies, `logs/run-*/` for what a particular run actually did.

**Start here:** `seeds.toml`. It is the file with rules attached to it.

---

## Files

```
  file                    what it is                            state
  ----------------------  ------------------------------------  -------
  seeds.toml              every random seed in the project,     current
                          in four sections: models,
                          uncertainty, evaluation, agent,
                          plus a global
  environment/            the interpreter this project is       current
    python-version        pinned to. Contains "3.11", which
                          agrees with requires-python in
                          pyproject.toml and with the CI
                          matrix
```

Both are hand-written and TRACKED. Neither is generated, and neither should
be edited casually.

## The rule

> Nothing in this project hardcodes a seed.

Every stochastic step reads its seed through `common.seeds.seed(section,
name)`, which parses this file once and caches it. Two consequences:

* Changing a seed is a deliberate act that shows up as a one-line diff in
  review, rather than being buried in a module somebody is editing for
  another reason.
* Asking for a seed that is not in the file RAISES. A missing seed fails
  loudly instead of quietly defaulting to zero and making two stages agree
  by accident. This is pinned by `tests/unit/test_seeds.py`.

## What is in seeds.toml

```
  section        keys
  -------------  -----------------------------------------------------
  global         seed
  models         hazard, zinb, lightgbm, synthetic_ctrl
  uncertainty    monte_carlo, bootstrap, conformal_split
  evaluation     train_test_split, label_noise_sim,
                 placebo_permutation
  agent          tool_sampling
```

Three of those name work that has not been built: `zinb` and `lightgbm` are
reserved for the successor specification and the gradient-boosted benchmark
(both now fitted — `docs/STATUS.md` §2), and `synthetic_ctrl` is reserved for
the
second estimand — the spatial difference-in-differences the original v3
proposal carried and nobody has touched. They are placeholders, not
evidence that those models exist.

## What is NOT here, and where it is instead

```
  the inputs           data/raw/manifest.jsonl - URL, SHA-256, byte
                       count and content type for every download
  the dependencies     pyproject.toml, with the reason each one is
                       present
  what a run did       logs/run-<id>/ - console.log, events.jsonl,
                       sql.jsonl, commands.jsonl, http.jsonl. Gitignored,
                       because a single un-scrubbed line could publish a
                       credential
  how to re-run it     docs/REPRODUCE.md
```
