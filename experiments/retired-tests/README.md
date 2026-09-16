# retired-tests

Eleven test files that came out of `tests/` when the code they protected came
out of `src/` on 2026-09-15 — the hazard model, the conformal machinery, the
portfolio optimiser and the agent gates. They are filed here beside those
programmes rather than deleted, because a retired module's tests are the
clearest statement of what it was supposed to do.

```
  test_hazard.py        test_risk_set.py       test_timebasis.py
  test_conformal.py     test_real_panel.py     test_optimize.py
  test_gates.py         test_agent_runner.py   test_montecarlo.py
  test_donor_pool_parsing.py                   test_warehouse_view.py
```

**Archived evidence, not a suite.** `pytest` does not collect them
(`testpaths = ["tests"]` in `pyproject.toml`) and they are not expected to pass
against the current `src/` — their imports point at modules that have moved to
[`../`](../). The 138 tests they contain are the difference between the
retired count of 798 and the current one; see `docs/NUMBERS.md` §12 and
[`../../tests/README.md`](../../tests/README.md).
