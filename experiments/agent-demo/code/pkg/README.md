# agent — the six-gate mutation path

L4. An agent proposes a change to the warehouse — a new facility, a
corrected address — and this package decides whether to apply it. Six gates
run in order, cheapest first, and every attempt is written to an audit
record including the ones that are rejected.

**Start here:** `gates.py`. It is 25 lines and it re-exports everything, so
it is the map. Then `gates_inference.py`, which is the part of this package
that is a contribution rather than an implementation of prior art.

---

## The claim this package makes

Gates 1-4 protect DATA integrity: the row is well-formed and truthful.
Every published agent-gating framework surveyed checks these, and the
project claims no novelty for them. Gates 5-6 protect INFERENTIAL
integrity: the estimator's assumptions still hold after the write. The
worked example in `gates_inference.py` is the whole argument — a competitor
sortation centre in Plano, Texas passes schema, geocoding, confidence and
audit-log checks, and still moves the donor pool, theta and the NPV by
millions. The data is fine; the inference is broken; nothing checked.

The two families live in separate modules because the distinction between
them IS the claim.

## Files

```
  file                purpose                                    state
  ------------------  -----------------------------------------  ------
  __init__.py         package note                               current
  types.py            the value objects: Mutation, GateResult,   works
                      Decision, Severity, and the Protects enum
                      that makes the data/inference boundary
                      explicit rather than a comment
  base.py             the contract every gate implements -       works
                      Gate (ABC) and WarehouseView (Protocol),
                      plus the valid facility types and
                      operators and the US bounding box
  gates_data.py       gates 1-4: schema conformance, geocoding,  works
                      extraction confidence, audit log. Prior
                      art, included for completeness
  gates_inference.py  gates 5-6: donor-pool integrity and        works
                      estimate stability. THE CONTRIBUTION
  estimators.py       what gate 6 re-runs, and what it does      works
                      when there is nothing to re-run.
                      UnavailableThetaEstimator RAISES and the
                      gate turns that into an ESCALATE, because
                      a gate that cannot run must not report a
                      pass
  pipeline.py         GatePipeline: sorts gates by number so     works
                      the cheap structural checks always run
                      before the expensive re-fit, and
                      assembles a Decision
  gates.py            re-exports all of the above unchanged      works
                      for callers. Read this first
  warehouse_view.py   the WarehouseView Protocol implemented     works
                      against the real DuckDB file. Kept out of
                      gates.py so the gate layer imports nothing
                      from the warehouse layer. The unit
                      conversion in neighbours_within (the
                      Protocol speaks km, the project's distance
                      function returns miles) and the donor-pool
                      fallback are the two places a
                      plausible-looking implementation is
                      quietly wrong
  runner.py           the CLI. Runs a proposed mutation through  works
                      the gates against real warehouse state
```

## Running it

```
  python -m siting_atlas.agent.runner --demo-plano
  python -m siting_atlas.agent.runner --mutation proposed.json
  python -m siting_atlas.agent.runner --mutation m.json --donor-pool d.txt
```

or `make agent` for the first of those.

Every invocation writes `outputs/audit/<mutation_id>.json` and appends to
`outputs/audit/mutations.jsonl`. Both, because the per-mutation file is what
a human opens and the JSONL is what an analysis reads. These are GENERATED —
hand edits are lost, and the JSONL is append-only across runs.

## Worth knowing

Gate 6 today escalates rather than passing, because it needs a fitted model
and `models/` does not currently have a specification anyone should refit
against (see `../models/README.md`). That escalation is the correct
behaviour and is asserted in `tests/unit/test_agent_runner.py`, in the test
named `test_unavailable_estimator_escalates_rather_than_passing`.

Nothing in this package is stale as far as this reading found.
