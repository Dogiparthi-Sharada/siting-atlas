# cost/ — L4 cost to serve

**This is the project's positive result.** It runs on real data, it
decomposes, and its sensitivity is reported across five scenarios. Everything
here is about *what it costs to deliver a parcel into a ZIP-code area*, and
none of it needs the target variable — which is why it kept working while the
prediction layer did not.

```bash
make cost          # python -m siting_atlas.cost.runner
```

Output: `outputs/tables/cost_to_serve_<period>_<scenario>.parquet` and
`outputs/metrics/cost_report.json`. **Quote the artefact and its `run_id`,
never a figure typed into a document.**

## Modules

```
  daganzo.py   the continuous approximation. You cannot solve a vehicle
               routing problem for 2,413 ZCTAs, so tour length is
               approximated analytically from stop density. The 1/sqrt(density)
               exponent is pinned by tests/unit/test_cost_daganzo_math.py,
               because getting it wrong leaves every number finite, positive
               and plausibly ordered -- and the ranking wrong
  depots.py    where the vans start from: a p-median NETWORK of depots, not
               one point per metro. K = ceil(metro daily parcels / 40,000),
               so the depot count is an external check rather than a second
               free parameter
  params.py    every assumption in one auditable place, each with its
               provenance and the direction of its bias
  runner.py    the L4 stage: run over the pilot, write the ranked output
```

## Three things to know before quoting it

**The depot proxy is the project's cleanest correction.** The first version
put one depot per metro at the population-weighted centroid and its own
docstring said the choice barely mattered — "at C=120 a ten-mile error moves
cost per parcel by well under a cent". Measured, the error was about
**twentyfold** that, the implied line hauls ran 0.4 to 145.7 miles, and the
model was substantially ranking distance-from-metro-centre. Full post-mortem:
[`docs/DECISION_LOG.md`](../../../docs/DECISION_LOG.md) §2.2.

**Cost per stop and cost per parcel are different quantities.** A stop carries
1.4 parcels and service time is paid once per door. Charging service time per
parcel overstates labour precisely in the dense ZCTAs the ranking exists to
identify as cheap.

**Two assumptions are still asserted rather than measured**, in exactly the
voice the depot docstring used: `income_elasticity = 0.35` ("set
conservatively") and `parcels_per_stop = 1.4`. Treat a docstring that says an
assumption does not matter as an open ticket.

The model from zero, with a worked two-ZCTA example and every parameter's
provenance, is [`docs/data/COST_MODEL.md`](../../../docs/data/COST_MODEL.md).
