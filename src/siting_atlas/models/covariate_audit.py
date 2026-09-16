"""What each candidate column IS, measured before anything is fitted.

Three properties decide whether a column can help a conditional choice
model at all, and two of them are fatal when they go the wrong way.

  CONSTANT WITHIN A METRO. The model only ever compares alternatives
  inside one choice set. A column with one value for the whole metro
  carries no information about which ZIP of that metro was chosen. It
  does not even cancel: added to every alternative it flattens the
  probabilities toward uniform, so the optimiser's only sensible move is
  to set its weight to zero. `wage_freight_handler` and `metro_employment`
  are exactly this — BLS OES is published at metro grain — which is why
  they are not offered as candidates.

  COUNTY GRAIN. `traffic_proximity`, `diesel_pm` and `permit_units_total`
  are county figures broadcast to every ZCTA of the county: EJScreen is a
  tract file with no tract-to-ZCTA crosswalk in L1 and is aggregated to
  county in `warehouse/optional.py`, and the Building Permits Survey is a
  county series joined on `county_geoid` in `warehouse/panel_sql.py`. A
  county-grain column cannot separate two ZIPs of the same county however
  good its theory is, and `mean_distinct_values_per_large_metro` measures
  how few distinct values a 200-alternative choice set actually sees.

  WITHIN-METRO COLLINEARITY WITH WHAT IS ALREADY IN. A raw national
  correlation mostly measures metro size. The only collinearity that can
  matter here is the kind that survives demeaning by metro, and a
  candidate that is a repackaging of a column already in the model shows
  up in it before a single fit is run.

`zctas_time_varying` is reported too, but it is NOT a screen. A
time-invariant column is a perfectly good attraction variable for a
model that never differences a ZCTA against its own past; it is fatal
only for a before/after design, which this is not.
"""

from __future__ import annotations

import pandas as pd

from .choice import ATTRACTIONS

__all__ = ["audit"]

#: A metro with more candidate ZIPs than this is the stratum the whole
#: experiment is about, and the grain questions are asked of it.
LARGE_METRO = 100


def audit(panel: pd.DataFrame, columns: tuple[str, ...]) -> dict:
    """Coverage, grain and within-metro collinearity for every column."""
    one = panel[panel["year"] == int(panel["year"].min())]
    one = one.drop_duplicates("zcta").dropna(subset=["cbsa_code"])
    sizes = one.groupby("cbsa_code")["zcta"].nunique()
    big = one[one["cbsa_code"].isin(sizes[sizes > LARGE_METRO].index)]
    out = {}
    for col in columns:
        have = big.dropna(subset=[col])
        per_metro = have.groupby("cbsa_code")[col].nunique()
        out[col] = {
            "populated_panel_wide": float(panel[col].notna().mean()),
            "zctas_time_varying": float(
                (panel.groupby("zcta")[col].nunique() > 1).mean()),
            "constant_within_large_metro": float((per_metro <= 1).mean()),
            "county_grain_share": float(
                (have.groupby("county_geoid")[col].nunique() <= 1).mean()),
            "mean_distinct_values_per_large_metro": float(per_metro.mean()),
            "within_metro_corr_with_baseline": _within_metro_corr(big, col),
        }
    return out


def _within_metro_corr(frame: pd.DataFrame, col: str) -> dict:
    """Correlation with each baseline column, demeaned by metro."""
    out = {}
    for base in ATTRACTIONS:
        if base == col:
            continue
        pair = frame[["cbsa_code", col, base]].dropna()
        if len(pair) < 3:
            out[base] = None
            continue
        dev = pair.groupby("cbsa_code")[[col, base]].transform(
            lambda s: s - s.mean())
        out[base] = float(dev[col].corr(dev[base]))
    return out


def print_audit(report: dict) -> None:
    """The screen, as a table, with the two fatal properties first."""
    print("\n  === candidate columns, before any fit ===\n")
    print(f"  {'column':30}{'popul':>8}{'time':>7}{'metro':>7}"
          f"{'county':>8}{'values':>8}{'r|estab':>9}{'r|hhold':>9}")
    for col, r in report.items():
        corr = r["within_metro_corr_with_baseline"]
        est = corr.get("establishments")
        hh = corr.get("households")
        print(f"  {col:30}{r['populated_panel_wide']:8.3f}"
              f"{r['zctas_time_varying']:7.2f}"
              f"{r['constant_within_large_metro']:7.2f}"
              f"{r['county_grain_share']:8.2f}"
              f"{r['mean_distinct_values_per_large_metro']:8.1f}"
              f"{(est if est is not None else float('nan')):9.3f}"
              f"{(hh if hh is not None else float('nan')):9.3f}")
    print("\n  popul   share of panel rows non-null")
    print("  time    share of ZCTAs whose value moves across panel years")
    print("  metro   share of LARGE metros where the column is constant")
    print("          (constant within the choice set = no information)")
    print("  county  share of counties with a single value = county grain")
    print("  values  mean distinct values per large metro choice set")
    print("  r|x     within-metro correlation with an in-model column")
