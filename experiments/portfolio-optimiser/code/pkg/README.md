# optimize/ — L4 portfolio selection

Given a capital budget, which ZCTAs should be activated? Not a ranking — a
**selection**, because activations interact: they share line haul and they
cannibalise each other's demand.

```bash
make optimize      # python -m siting_atlas.optimize.runner --budget 2e9
```

Minutes, not seconds, which is why it is deliberately outside `make all`.
Output: `outputs/tables/portfolio_<period>.parquet` and
`outputs/metrics/portfolio_report.json`. **Read `detail.n`, `detail.capital`
and `optimality_gap` out of the artefact with its `run_id`** — this headline
has moved three times and every document that hardcoded it had to be redone.

## Modules

```
  objective.py   what a portfolio is worth. NPV(S) = m*A(S) - B(S) - K(S),
                 with saturating cannibalisation `peak * (1 - exp(-exposure))`
  select.py      greedy plus a pairwise local swap, with a computed upper
                 bound and a real stopping rule (marginal NPV <= 0)
  params.py      how activations interact and what they cost, separated from
                 the objective so a reviewer can read the assumptions without
                 reading the search
  montecarlo.py  500 draws over every documented cost and portfolio parameter,
                 each re-solving the cost model and the optimiser
  runner.py      the L4 stage
```

## Four things to know

**No `(1 - 1/e)` guarantee is claimed.** The objective has both positive and
negative interactions, so it is not submodular and the bound does not apply.
The reported gap is instance-specific, against a computed upper bound.

**The margin is unobservable, so the deliverable is a frontier.** NPV is
linear in the contribution margin, so choosing one value would choose the
answer. `--margin` defaults to the break-even of a full-budget portfolio,
which is self-referential rather than arbitrary; `--frontier` solves at six
margins.

**The headline finding is that it declines to spend the budget.** The
remaining activations lose money at the neutral margin. The previous
objective — minimise the portfolio's break-even margin — was degenerate and
minimised at n = 1; it could not express "this activation destroys value".
Post-mortem: [`docs/DECISION_LOG.md`](../../../docs/DECISION_LOG.md) §2.5.

**`objective.py` does not know what an activation is, and this is an open
defect.** Three lines price the same object three ways: `:81-83` as a ZCTA of
resident demand, `:164` as a facility, `:158` as a facility with a catchment.
Measured consequence: ~2.7× capital overcharge. It is the same
unit-of-analysis error that killed the hazard model, in a second component.
[`docs/STATUS.md`](../../../docs/STATUS.md) §6.

**The Monte Carlo is not a confidence interval.** Every range comes from
`docs/data/PARAMETERS.md` and was chosen by this project, eight constants with
no external source, so it propagates our priors and not the world's. And
`parcels_per_depot_per_day` was never sampled (`montecarlo.py:128,137`,
"excluded by oversight"), so every band is a floor.
