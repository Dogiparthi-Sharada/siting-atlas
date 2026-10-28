"""Fit the household demand model on NHTS and test it on households it never saw.

Model (Poisson regression, log link, survey-weighted):
  log E[deliveries per month] = b0 + b1 ln(income) + b2 household size
                                + b3 renter + b4 workers + b5 ln(density)
                                + b6 mean adult age
b1 is directly the income elasticity: 1% more income -> b1 % more deliveries.

Writes model_<year>.json (coefficients, refit on all households) and prints
the hold-out tests.
"""
import json
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
from nhts_load import load

HERE = os.path.dirname(os.path.abspath(__file__))
X = ["ln_income", "hh_size", "renter", "workers", "ln_density", "adult_age"]


def _fit(df):
    w = df.w * len(df) / df.w.sum()
    return sm.GLM(df.y, sm.add_constant(df[X]), family=sm.families.Poisson(),
                  freq_weights=w).fit(cov_type="HC1")


def _deviance(y, mu, w):
    y, mu = np.asarray(y, float), np.asarray(mu, float)
    term = np.where(y > 0, y * np.log(np.where(y > 0, y, 1) / mu), 0.0) - (y - mu)
    return 2 * np.sum(w * term)


def _calibration(test, mu, by):
    g = test.assign(mu=mu).groupby(by)
    return pd.DataFrame({
        "households": g.size(),
        "observed": g.apply(lambda t: np.average(t.y, weights=t.w), include_groups=False),
        "predicted": g.apply(lambda t: np.average(t.mu, weights=t.w), include_groups=False),
    }).round(2)


def run(year):
    df = load(year)
    rng = np.random.default_rng(20261028)
    test_mask = rng.random(len(df)) < 0.2
    train, test = df[~test_mask], df[test_mask]
    m = _fit(train)
    mu = m.predict(sm.add_constant(test[X]))
    null = np.average(train.y, weights=train.w)
    w = test.w / test.w.mean()
    dev_m, dev_0 = _deviance(test.y, mu, w), _deviance(test.y, np.full(len(test), null), w)
    mae_m = np.average(np.abs(test.y - mu), weights=test.w)
    mae_0 = np.average(np.abs(test.y - null), weights=test.w)

    print(f"\n================ NHTS {year} ================")
    print(f"households: train {len(train):,}  hold-out {len(test):,}")
    print(f"hold-out deviance explained vs 'everyone gets the average': {1 - dev_m / dev_0:.1%}")
    print(f"hold-out mean absolute error: model {mae_m:.2f}  average-only {mae_0:.2f} deliveries/month")
    print("hold-out calibration by income bracket (deliveries/month):")
    print(_calibration(test, mu, "income_bracket").to_string())
    print("hold-out calibration by predicted fifth (lowest -> highest):")
    print(_calibration(test, mu, pd.qcut(mu, 5, labels=[1, 2, 3, 4, 5])).to_string())

    full = _fit(df)
    ci = full.conf_int()
    print("coefficients, all households (95% CI):")
    for k in ["const"] + X:
        print(f"  {k:11s} {full.params[k]:9.4f}  [{ci.loc[k, 0]:8.4f}, {ci.loc[k, 1]:8.4f}]"
              f"   x{np.exp(full.params[k]):.3f} per unit")
    out = {"year": year, "households": len(df), "features": X,
           "params": full.params.to_dict(), "ci_low": ci[0].to_dict(), "ci_high": ci[1].to_dict(),
           "mean_deliveries_month": float(np.average(df.y, weights=df.w)),
           "holdout": {"deviance_explained": float(1 - dev_m / dev_0),
                       "mae_model": float(mae_m), "mae_average": float(mae_0),
                       "n_train": int(len(train)), "n_test": int(len(test))}}
    with open(os.path.join(HERE, f"model_{year}.json"), "w") as fh:
        json.dump(out, fh, indent=2)


if __name__ == "__main__":
    for yr in (2022, 2017):
        run(yr)
