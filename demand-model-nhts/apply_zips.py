"""Apply the fitted NHTS model to every ZIP, scale to Amazon, and rerun the
station-workload and cost checks against the old formula.

Design: NHTS decides WHERE demand is (each ZIP's deliveries per household
relative to the national average); Pitney Bowes decides HOW MUCH (Amazon
Logistics 6.3bn parcels in 2024 over ~135m households = 0.90 per household
per week, both from the 2026 Parcel Shipping Index).

Run from the siting-atlas folder with its venv (needs the project package).
"""
import dataclasses
import json
import os
import sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from siting_atlas.cost import station_runner as sr                      # noqa: E402
from siting_atlas.cost.params import BASELINE                           # noqa: E402
from siting_atlas.cost.stations import StationCostModel, StationNetwork  # noqa: E402

AMAZON_PARCELS_2024 = 6.3e9
US_HOUSEHOLDS = 23.1e9 / 171            # PB 2025 volume / PB parcels per household
AMAZON_RATE = AMAZON_PARCELS_2024 / US_HOUSEHOLDS / 52
DAYS, LOW, HIGH = BASELINE.delivery_days_per_week, 20_000, 60_000
YEAR = int(os.environ.get("NHTS_YEAR", 2022))


def zip_index(z, model):
    """Each ZIP's predicted deliveries per household, relative to the US average."""
    p = model["params"]
    x = pd.DataFrame({
        "ln_income": np.log(z.median_household_income.fillna(BASELINE.reference_income_usd)),
        "hh_size": z.hh_size.clip(1, 7),
        "renter": z.renter_share.fillna(z.renter_share.median()),
        "workers": z.workers_per_hh.clip(0, 4),
        "ln_density": np.log(z.hh_per_sqmi.clip(50, 30_000)),
        "adult_age": z.median_age.fillna(z.median_age.median()),
    })
    lin = p["const"] + sum(p[k] * x[k] for k in model["features"])
    per_hh = np.exp(lin)
    return per_hh / np.average(per_hh, weights=z.households)


def old_index(z):
    inc = z.median_household_income.fillna(BASELINE.reference_income_usd)
    return (inc / BASELINE.reference_income_usd) ** BASELINE.income_elasticity


class _FixedDemand(StationCostModel):
    def __init__(self, params, station_miles, parcels):
        super().__init__(params, station_miles)
        self._parcels = parcels

    def daily_parcels(self, frame):
        return self._parcels.reindex(frame.index)


def station_loads(costed, parcels, net):
    s = pd.Series(parcels.values, index=costed["station_id"].values).groupby(level=0).sum()
    per = s.rename("demand").to_frame().join(net.stations.set_index("station_id")[["state"]])
    per["band"] = pd.cut(per.demand, [0, LOW, HIGH, 1e12], labels=["below", "within", "above"])
    return per


def main():
    model = json.load(open(os.path.join(HERE, f"model_{YEAR}.json")))
    z = pd.read_parquet(os.path.join(HERE, "zip_features.parquet"))
    z["idx_new"] = zip_index(z, model).values
    z["idx_old"] = old_index(z).values
    z["amazon_daily_new"] = z.households * AMAZON_RATE * z.idx_new / DAYS
    z["amazon_daily_old"] = z.households * 0.9 * z.idx_old / DAYS
    z.to_parquet(os.path.join(HERE, f"zip_demand_{YEAR}.parquet"), index=False)

    print(f"model NHTS {YEAR}; Amazon rate {AMAZON_RATE:.3f} parcels/household/week (PB 2024)")
    print(f"ZIPs {len(z):,}  households {z.households.sum():,.0f}")
    print(f"national Amazon parcels/yr implied: new {z.amazon_daily_new.sum() * DAYS * 52 / 1e9:.2f}bn"
          f"   old {z.amazon_daily_old.sum() * DAYS * 52 / 1e9:.2f}bn")
    print(f"old formula average multiplier {np.average(z.idx_old, weights=z.households):.3f} "
          f"(new is 1.000 by construction)")
    rho = z[["idx_new", "idx_old"]].corr(method="spearman").iloc[0, 1]
    ratio = z.idx_new / z.idx_old
    print(f"per-household demand, new vs old: rank correlation {rho:.3f}; "
          f"ZIPs moved >20%: {(abs(ratio - 1) > .2).mean():.1%} "
          f"(households in them {z.households[abs(ratio - 1) > .2].sum() / z.households.sum():.1%})")
    print("new/old per-household ratio, p10 / median / p90:",
          " / ".join(f"{ratio.quantile(q):.2f}" for q in (.1, .5, .9)))
    for code in ["95140", "89084", "10069"]:
        r = z[z.zcta == code]
        if len(r):
            r = r.iloc[0]
            print(f"  ZIP {code}: hh {r.households:,.0f}  income {r.median_household_income:,.0f}  "
                  f"size {r.hh_size:.2f}  renters {r.renter_share:.0%}  "
                  f"Amazon/day new {r.amazon_daily_new:,.0f}  old {r.amazon_daily_old:,.0f}")

    frame = sr.national_slice(2023, 4)
    net = StationNetwork.load()
    costed, _, _ = sr.build_catchment(frame, net)
    zz = z.set_index("zcta")
    new = pd.Series(zz.amazon_daily_new.reindex(costed.zcta).values, index=costed.index)
    old = pd.Series(zz.amazon_daily_old.reindex(costed.zcta).values, index=costed.index)
    assert new.notna().all() and old.notna().all(), "costed ZIP missing from feature table"

    print("\nSTATION WORKLOADS (Amazon parcels/day; real range 20,000-60,000)")
    rows = []
    for name, parcels in [("old formula", old), ("NHTS model", new)]:
        per = station_loads(costed, parcels, net)
        b = per.band.value_counts()
        st = per.groupby("state").demand.agg(["size", "mean"])
        big = st[st["size"] >= 5]
        inside = int(((big["mean"] >= LOW) & (big["mean"] <= HIGH)).sum())
        print(f"  {name:12s} stations {len(per)}  median {per.demand.median():,.0f}  "
              f"p10 {per.demand.quantile(.1):,.0f}  p90 {per.demand.quantile(.9):,.0f}  "
              f"below {b['below']}  within {b['within']}  above {b['above']}  "
              f"states(5+) inside {inside} of {len(big)}")
        rows.append(per.demand.rename(name))
    pd.concat(rows, axis=1).round(0).to_csv(os.path.join(HERE, f"station_loads_{YEAR}.csv"))

    print("\nCOST PER PARCEL (median over costed ZIPs)")
    for name, parcels in [("old formula", old), ("NHTS model", new)]:
        c = _FixedDemand(BASELINE, costed["station_miles"], parcels).evaluate(costed)["cost_per_parcel"]
        print(f"  {name:12s} ${c.median():.4f}   p10 ${c.quantile(.1):.2f}   p90 ${c.quantile(.9):.2f}")
    p12 = dataclasses.replace(BASELINE, parcels_per_stop=1.2)
    c = _FixedDemand(p12, costed["station_miles"], new).evaluate(costed)["cost_per_parcel"]
    print(f"  NHTS model, parcels/stop 1.2: ${c.median():.4f}")


if __name__ == "__main__":
    main()
