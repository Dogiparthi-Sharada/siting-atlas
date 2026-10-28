"""Household table from the NHTS public files: one row per household with
monthly online deliveries (the target), the features that also exist per ZIP
in the ACS, and the survey weight.

Target
  2022  sum over members of DELIV_GOOD ("times goods delivered, past 30 days")
  2017  sum over members of DELIVER ("times purchased online for delivery,
        past 30 days"); 2017 has no goods-only split
  Members skipped by design (code -1: children, or DELIVER = 0 in 2022) count
  as zero. A household with any member coded -7/-8/-9 (refused, don't know,
  not ascertained) is dropped, so totals are never silently partial.

Codes that the data dictionary does not label, and how they were settled, are
listed in CODES below and reported by check_codes().
"""
import os
import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
# Scratch copy keeps the data in ./sources; inside siting-atlas it lives in data/raw.
SRC = os.path.join(_HERE, "sources")
if not os.path.isdir(SRC):
    SRC = os.path.join(_HERE, "..", "..", "data", "raw")

# Standard NHTS income brackets (lower-upper, USD); midpoints, $250k for 200k+.
INCOME_MID = {1: 5_000, 2: 12_500, 3: 20_000, 4: 30_000, 5: 42_500, 6: 62_500,
              7: 87_500, 8: 112_500, 9: 137_500, 10: 175_000, 11: 250_000}
# Housing units per sq mi of the home block group. 2017 stores the category
# midpoint itself; 2022 stores the category number 1-8 in the same order.
DENSITY_2022 = {1: 50, 2: 300, 3: 750, 4: 1500, 5: 3000, 6: 7000, 7: 17000, 8: 30000}
CODES = {"renter_2017": {2}, "renter_2022": {3}}


def _household(year):
    d = os.path.join(SRC, f"nhts{year}")
    hh_file, per_file = ("hhv2pub.csv", "perv2pub.csv") if year == 2022 else ("hhpub.csv", "perpub.csv")
    target = "DELIV_GOOD" if year == 2022 else "DELIVER"
    p = pd.read_csv(os.path.join(d, per_file), usecols=["HOUSEID", "R_AGE", "DELIVER", target])
    h = pd.read_csv(os.path.join(d, hh_file), usecols=["HOUSEID", "WTHHFIN", "HHFAMINC", "HHSIZE",
                                                       "WRKCOUNT", "HOMEOWN", "HBRESDN", "URBRUR"])
    if year == 2022:   # DELIV_GOOD is skipped (-1) when DELIVER is 0 or the person is a child
        p["y"] = p[target].where(p[target] != -1, 0)
        bad = (p[target] < -1) | (p.DELIVER < -1)
    else:
        p["y"] = p[target].where(p[target] != -1, 0)
        bad = p[target] < -1
    drop = p.loc[bad, "HOUSEID"].unique()
    adults = p[p.R_AGE >= 18].groupby("HOUSEID").R_AGE.mean().rename("adult_age")
    y = p.groupby("HOUSEID").y.sum()
    h = h.set_index("HOUSEID").join(y).join(adults)
    h = h[~h.index.isin(drop)]
    density = h.HBRESDN.map(DENSITY_2022) if year == 2022 else h.HBRESDN.where(h.HBRESDN > 0)
    out = pd.DataFrame({
        "y": h.y,
        "w": h.WTHHFIN,
        "income_bracket": h.HHFAMINC,
        "ln_income": np.log(h.HHFAMINC.map(INCOME_MID)),
        "hh_size": h.HHSIZE.clip(upper=7),
        "workers": h.WRKCOUNT.clip(lower=0, upper=4),
        "renter": h.HOMEOWN.isin(CODES[f"renter_{year}"]).astype(int),
        "ln_density": np.log(density),
        "adult_age": h.adult_age,
        "urban": (h.URBRUR == 1).astype(int),
        "homeown_code": h.HOMEOWN,
    }, index=h.index)
    return out.dropna(subset=["y", "ln_income", "ln_density", "adult_age"])


def load(year):
    return _household(year)


def check_codes(df, year):
    """Weighted shares that settle the unlabelled codes against known US figures."""
    w = df.w / df.w.sum()
    print(f"--- {year}: {len(df):,} households kept")
    print("  HOMEOWN weighted shares:", w.groupby(df.homeown_code).sum().round(3).to_dict())
    print("  income bracket weighted shares:", w.groupby(df.income_bracket).sum().round(3).to_dict())
    print(f"  urban share {np.average(df.urban, weights=df.w):.3f}   "
          f"mean deliveries/month {np.average(df.y, weights=df.w):.2f}")


if __name__ == "__main__":
    for yr in (2022, 2017):
        check_codes(load(yr), yr)
