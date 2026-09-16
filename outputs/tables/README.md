# outputs/tables — the per-ZCTA result parquets

Eight parquet files. **All generated**; a hand edit is lost at the next run of
the stage that wrote it. These are the rows behind every chart in
[`../figures/`](../figures/), every summary in `../metrics/cost_report.json`,
and the dashboard (`make app` refuses to start without them).

## What is here

| file | rows | written by |
|---|---|---|
| `cost_to_serve_2023q4_baseline.parquet` | 2,333 | `make cost` |
| `cost_to_serve_2023q4_congested.parquet` | 2,333 | `make cost` |
| `cost_to_serve_2023q4_dense_routing.parquet` | 2,333 | `make cost` |
| `cost_to_serve_2023q4_high_fuel.parquet` | 2,333 | `make cost` |
| `cost_to_serve_2023q4_pessimistic_tour.parquet` | 2,333 | `make cost` |
| `portfolio_2023q4.parquet` | 282 | `siting_atlas.optimize.runner` — **retired to `experiments/portfolio-optimiser/`** |
| `hazard_predictions.parquet` | 8,044 | `siting_atlas.models.runner` — **retired to `experiments/hazard-model/`** |
| `montecarlo_draws.parquet` | 500 | `siting_atlas.optimize.montecarlo` — **retired to `experiments/portfolio-optimiser/`** |

The five `cost_to_serve_*` files are the live output: one row per pilot ZCTA
per scenario, one file per scenario, all produced by
`python -m siting_atlas.cost.runner --all-scenarios`. The scenarios are
described in [`../figures/README.md`](../figures/README.md).

The other three are left in place from before their stages were archived on
2026-09-15. Their emitters are no longer in `src/siting_atlas`; the code and
the findings are under [`../../experiments/`](../../experiments/). They cannot
be regenerated from this tree without restoring that code.

## The cost table's columns

Same 23 columns in every `cost_to_serve_*` file. `portfolio_2023q4.parquet`
is the baseline table plus one boolean, `selected`.

```
  column                       unit              what it is
  ---------------------------  ----------------  ------------------------------
  rank                         —                 position after sorting by
                                                 cost_per_parcel, cheapest = 1
  zcta                         string            5-digit ZCTA, zero-padded
  daily_parcels                parcels / day     modelled demand
  daily_stops                  stops / day       daily_parcels / parcels_per_stop
  stop_density_per_sqmi        stops / sq mi     daily_stops / land area
  linehaul_miles               miles             depot to ZCTA, one way
  local_miles_per_stop         miles / stop      the Daganzo BHH term
  linehaul_miles_per_stop      miles / stop      2 * linehaul / stops_per_tour
  miles_per_stop               miles / stop      local + linehaul
  cost_distance                USD / stop        fuel and maintenance
  cost_drive_time              USD / stop        loaded driver wage, driving
  cost_service_time            USD / stop        loaded driver wage, at the door
  cost_vehicle                 USD / stop        daily van lease / stops_per_tour
  cost_per_stop                USD / stop        the four components summed
  cost_per_parcel              USD / parcel      cost_per_stop / parcels_per_stop
  daily_cost_usd               USD / day         cost_per_stop * daily_stops
  van_days                     van-days / day    daily_stops / stops_per_tour,
                                                 deliberately FRACTIONAL
  vans_required                vans              van_days rounded up. Do NOT sum
                                                 this across ZCTAs
  income_imputed               bool              median household income was
                                                 missing and was imputed
  metro_label                  string            CBSA name
  state                        string            2-letter postal code
  population                   people            ZCTA population
  land_area_sqmi               sq mi             ZCTA land area
```

**The four `cost_*` components are costs per STOP, not per parcel.** A parcel
is cheaper than a stop whenever more than one arrives at the same door;
`cost_per_parcel` is the divided figure and is the one the headline quotes.

**`vans_required` must not be summed.** It is the "if this ZCTA had a
dedicated van" reading. 145 sparse ZCTAs each rounding up to a whole van
overstates the fleet by a wide margin. Aggregate `van_days` and round up once,
which is what `cost_report.json:total_vans` does.

## The other three

```
  hazard_predictions.parquet   zcta, t, event, hazard, set_includes_0,
                               set_includes_1, synthetic -- the per-row
                               output of the discrete-time hazard model that
                               was retired. Real output of a real fit, and
                               output you should not build a claim on
  portfolio_2023q4.parquet     the baseline cost table plus `selected`, the
                               greedy portfolio's choice under a $2bn budget
  montecarlo_draws.parquet     500 draws: `draw`, `ok`, five outcomes (n,
                               capital_usd, breakeven_margin, optimality_gap,
                               median_cost_per_parcel) and 21 sampled
                               parameters, prefixed `p_` (6 portfolio) and
                               `c_` (15 cost model)
```

Read [`../../experiments/README.md`](../../experiments/README.md) before
quoting anything from these three — it says why each programme was retired.

## Source of truth

For any figure derived from these tables,
[`../../docs/NUMBERS.md`](../../docs/NUMBERS.md) is the tie-breaker.
