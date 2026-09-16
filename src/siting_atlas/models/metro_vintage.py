"""Which year a covariate was OBSERVED, and the gate that uses it.

Prereg `docs/PREREG_METRO_MODEL.md` section 4: "Everything here must be
available **strictly before** the year being predicted", and section 8.1
makes the failure to enforce that an invalidating condition, with the
instruction that a column which cannot be enforced "is dropped and the drop
is counted".

This file is the enforcement. It carries no judgement about whether a column
is *useful*; it records, per column, the single fact the gate needs — the
latest calendar year whose information the column can contain — and where
that fact was read from, so the claim is auditable rather than asserted.

The reason this matters more here than it looks
-----------------------------------------------
Most of the panel's columns are SINGLE-VINTAGE broadcasts. Measured on
`data/processed/panel.parquet`, the mean number of distinct values per ZCTA
across all 32 quarters is 1.00 for population, households,
median_household_income, traffic_proximity and diesel_pm, and for the four
wage columns plus metro_employment. One value, repeated across eight years.
That is not a time series. It is one observation from one vintage, and the
vintage is later than most of the years being predicted:

    ACS 5-year 2023          published Dec 2024, covers 2019-2023
    BLS OES  oesm25ma.zip    May 2025 reference period
    EJScreen 2024            released 2024
    Census BPS               genuinely annual, one row per county-year
    EIA / Zillow             genuinely monthly

So using `households` to predict 2020 is not a borderline call about
publication lag. The figure is built from survey responses collected in
2019-2023, three of which are after the outcome. This is the same shape of
error as `NOTES_COVARIATE_LEAKAGE.md`, where a guard that looked real was
defeated by a median 34 months.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["VINTAGES", "Vintage", "usable_for", "gate"]


@dataclass(frozen=True)
class Vintage:
    """The latest year a column's information can reach, and the evidence."""

    #: ``None`` means the column is genuinely annual and its value for year
    #: Y contains only year-Y information; the gate then compares Y itself.
    fixed_year: int | None
    source: str
    evidence: str

    @property
    def time_varying(self) -> bool:
        return self.fixed_year is None

    def to_dict(self) -> dict:
        return {"fixed_year": self.fixed_year, "source": self.source,
                "evidence": self.evidence, "time_varying": self.time_varying}


_ACS = "ACS 5-year, data/interim/acs5_zcta_2023.parquet"
_OES = "BLS OES, data/external/bls_oes/oesm25ma.zip"
_EJ = "EPA EJScreen, data/external/ejscreen/EJScreen_2024_Tract_*.csv.zip"
_BPS = "Census Building Permits Survey, data/interim/building_permits.parquet"
_FAC = "data/external/facility_panel/national_facilities_expanded.csv"

#: One entry per covariate named in prereg section 4. Nothing else is
#: admissible: the prereg fixed the list, so adding a column here after
#: seeing a result would be the selection error the prereg exists to stop.
VINTAGES: dict[str, Vintage] = {
    # --- Tier 1: the columns that failed at ZIP grain because coarse ------
    "permit_units_total": Vintage(
        None, _BPS,
        "year column runs 2017-2025; one value per county-year"),
    "permits_yoy_pct": Vintage(
        None, _BPS,
        "derived from two consecutive BPS years"),
    "wage_freight_handler": Vintage(
        2025, _OES,
        "oesm25ma.zip = May 2025 reference; 1 distinct value per CBSA"),
    "wage_all_occupations": Vintage(
        2025, _OES,
        "oesm25ma.zip = May 2025 reference; 1 distinct value per CBSA"),
    "metro_employment": Vintage(
        2025, _OES,
        "oesm25ma.zip = May 2025 reference; 1 distinct value per CBSA"),
    "traffic_proximity": Vintage(
        2024, _EJ,
        "EJScreen_2024 release; 1 distinct value per ZCTA over 32 quarters"),
    "diesel_pm": Vintage(
        2024, _EJ,
        "EJScreen_2024 release; 1 distinct value per ZCTA over 32 quarters"),
    # --- Tier 2: scale and demand ----------------------------------------
    "households": Vintage(
        2023, _ACS,
        "acs_year == 2023, 5-year sample covering 2019-2023"),
    "population": Vintage(
        2023, _ACS,
        "acs_year == 2023, 5-year sample covering 2019-2023"),
    "median_household_income": Vintage(
        2023, _ACS,
        "acs_year == 2023, 5-year sample covering 2019-2023"),
    # --- Tier 3: the existing network, time-respecting --------------------
    "facilities_open_prior": Vintage(
        None, _FAC,
        "counted from open_year <= t-1 at construction time"),
    "dist_nearest_outside_prior": Vintage(
        None, _FAC,
        "nearest facility with open_year <= t-1 in another CBSA"),
}


def usable_for(column: str, predict_year: int) -> bool:
    """True if `column` can be known strictly before `predict_year`.

    A time-varying column is read at lag 1 by the frame builder, so the
    value carried on row (metro, t) is the t-1 observation and the test is
    automatically satisfied. A fixed-vintage column must have been observed
    in a year strictly earlier than the one being predicted.
    """
    v = VINTAGES[column]
    if v.time_varying:
        return True
    return v.fixed_year < predict_year


def gate(columns: list[str], years: list[int]) -> dict:
    """Split `columns` into those usable in EVERY year of `years`, and not.

    "Every year" rather than "this year" on purpose. A covariate set that
    changes shape between held-out years is a different model per year, and
    the per-year AUCs would then not be comparable to each other. The prereg
    asks for one model rolled forward, so the admissible set is the
    intersection over the evaluation window.
    """
    kept, dropped = [], {}
    for c in columns:
        ok = [y for y in years if usable_for(c, y)]
        if len(ok) == len(years):
            kept.append(c)
        else:
            v = VINTAGES[c]
            dropped[c] = {
                "fixed_year": v.fixed_year,
                "source": v.source,
                "evidence": v.evidence,
                "usable_years": ok,
                "blocked_years": [y for y in years if y not in ok],
            }
    return {"kept": kept, "dropped": dropped,
            "n_kept": len(kept), "n_dropped": len(dropped)}
