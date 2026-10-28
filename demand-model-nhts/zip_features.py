"""ZIP side of the demand model: one row per ZCTA, the household characteristics
the NHTS model will be fitted on, built from the ACS already in the project.

Proxies, to be matched to the NHTS definitions once the codebook arrives:
  workers_per_hh   ACS labour force (not employed workers) / households
  bachelors_share  bachelor's degree holders / total population
                   (ACS counts adults 25+; no 25+ denominator is cached)
  urban            households per sq mi >= 500, a density stand-in for the
                   Census urban/rural flag NHTS uses
"""
import os
from siting_atlas.cost import station_runner as sr

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zip_features.parquet")

f = sr.national_slice(2023, 4)
f = f[(f.households > 0) & (f.land_area_sqmi > 0)].copy()
z = f[["zcta", "state", "cbsa_code", "households", "land_area_sqmi",
       "median_household_income", "median_age"]].copy()
z["hh_size"] = f.population / f.households
z["renter_share"] = f.renter_occupied / (f.owner_occupied + f.renter_occupied)
z["bachelors_share"] = f.bachelors_degree / f.population
z["workers_per_hh"] = f.in_labor_force / f.households
z["hh_per_sqmi"] = f.households / f.land_area_sqmi
z["urban"] = (z.hh_per_sqmi >= 500).astype(int)
z.to_parquet(OUT, index=False)

print(f"ZCTAs {len(z):,}  households {z.households.sum():,.0f}  -> {OUT}")
print(z.drop(columns=["zcta", "state", "cbsa_code"]).describe(percentiles=[.1, .5, .9]).T
      [["count", "10%", "50%", "90%"]].round(2).to_string())
print(f"\nmissing income {z.median_household_income.isna().mean():.1%}   "
      f"missing age {z.median_age.isna().mean():.1%}   "
      f"households in 'urban' ZCTAs {z.households[z.urban == 1].sum() / z.households.sum():.1%}")
