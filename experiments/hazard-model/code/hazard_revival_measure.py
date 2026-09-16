"""What the expanded facility frame measures, before anything is fitted.

Split from ``hazard_revival_frames`` when that module crossed 300 lines. The
seam is real: everything here is a MEASUREMENT taken on the facility frame or
the panel, and nothing here builds an estimation sample. Three of these
functions exist because a claim in the brief needed checking rather than
quoting — the 34-month dating lag, the ZCTAs-per-opening count, and the
catchment-radius lever — and the fourth refuses to let the run proceed if
the target rebuild disagrees with the delivered panel.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..warehouse.catchment_band import BASELINE_MILES, catchment_pairs
from ..warehouse.catchment_band import enabled_at as _enabled_at
from .hazard_revival_frames import COVARIATES_5


def date_gap(fac: pd.DataFrame) -> dict:
    """How late the OSHA bound runs against the date the frame carries.

    Measured here rather than quoted, on the facilities that carry both. The
    national rows are split out because their "frame date" was DERIVED from
    the bound, so a gap of zero there is an identity and not a measurement.
    """
    bound = pd.to_datetime(fac["osha_operating_by"], errors="coerce")
    both = fac.loc[bound.notna() & fac["open_year"].notna()]
    if both.empty:
        return {"n": 0, "reason": "no facility carries both a date and "
                                  "an OSHA bound"}
    stamp = bound.loc[both.index]
    gap = ((stamp.dt.year * 4 + stamp.dt.quarter - 1)
           - (both["open_year"] * 4 + both["open_quarter"].fillna(1) - 1))

    def block(mask: pd.Series) -> dict:
        g = gap[mask]
        if g.empty:
            return {"n": 0}
        return {"n": int(len(g)),
                "median_quarters": float(g.median()),
                "median_months": float(g.median() * 3),
                "mean_months": round(float(g.mean() * 3), 1),
                "pct_over_one_year": round(100.0 * float((g > 4).mean()), 1)}

    mwpvl = both["source_dataset"].eq("mwpvl_2025q1")
    return {
        "all_with_both": block(pd.Series(True, index=both.index)),
        "mwpvl_dated": block(mwpvl),
        "national_dated": block(~mwpvl),
        "note": "The national rows were BUILT by classifying the OSHA "
                "extract, so their gap of zero is an identity, not a "
                "measurement. Only the mwpvl_dated block measures anything.",
    }


def catchment_load(fac: pd.DataFrame, geo: pd.DataFrame,
                   miles: float = BASELINE_MILES) -> dict:
    """How many ZCTAs one opening switches on, on THIS frame.

    Two counts, and the gap between them is the point.

    ``zctas_per_opening`` is the raw catchment: every ZCTA within the radius
    of a station. That is the number of cells one leasing decision moves.

    ``zctas_first_switched_on`` counts only the ZCTAs for which this station
    is the EARLIEST to arrive, which is what registers as an event in the
    risk set. On a national frame most catchments overlap, so the second
    number is much smaller than the first. That is not an improvement: the
    overlap means a ZCTA's switch-on quarter is a function of several
    stations' decisions at once, which is a second dependence on top of the
    one the retirement was taken on.
    """
    cover = catchment_pairs(fac, geo, miles)
    if cover.empty:
        return {"radius_miles": miles, "facilities_attached": 0}
    per = cover.groupby("facility_id")["zcta"].nunique()
    first = cover.groupby("zcta")["open_q_index"].min().rename("first_open")
    setters = cover.merge(first, on="zcta")
    setters = setters[setters["open_q_index"] == setters["first_open"]]
    sets = setters.groupby("facility_id")["zcta"].nunique()
    per_zcta = cover.groupby("zcta")["facility_id"].nunique()
    return {
        "radius_miles": miles,
        "facilities_attached": int(per.size),
        "zctas_covered": int(per_zcta.size),
        "zctas_per_opening": {
            "median": float(per.median()), "mean": round(float(per.mean()), 1),
            "p10": float(per.quantile(0.10)),
            "p90": float(per.quantile(0.90)), "max": int(per.max())},
        "zctas_first_switched_on": {
            "n_facilities": int(sets.size),
            "median": float(sets.median()),
            "mean": round(float(sets.mean()), 1), "max": int(sets.max())},
        "pct_zctas_served_by_2plus": round(
            100.0 * float((per_zcta > 1).mean()), 1),
    }


def catchment_load_band(fac: pd.DataFrame, geo: pd.DataFrame,
                        radii=(8.3, 12.7, 15.0, 19.6, 25.0, 45.0)) -> dict:
    """:func:`catchment_load` across ``catchment_band.RADII``.

    ``outputs/metrics/catchment_band.json`` measured a 4.76x lever on enabled
    cells across the 8.3-45 mile band and found the conclusion unchanged at
    every radius — on the PILOT frame. The radius itself has not moved (15
    miles, ``facilities.CATCHMENT_MILES``), so this re-measures only the
    thing the independence argument turns on: how many ZCTAs one opening
    moves. No refit; the fits below all sit at 15 miles.
    """
    points = [{"radius_miles": m, **catchment_load(fac, geo, m)}
              for m in radii]
    cells = [p["zctas_covered"] for p in points]
    return {"points": points,
            "zctas_covered_ratio_high_low": round(
                max(cells) / min(cells), 2) if min(cells) else None,
            "note": "Measured on the expanded frame. The fits all use 15 "
                    "miles; this band says only how far the unit-of-analysis "
                    "problem travels with the radius, and it never reaches "
                    "one ZCTA per opening."}


def truncation_cost(panel: pd.DataFrame, fac: pd.DataFrame,
                    geo: pd.DataFrame,
                    miles: float = BASELINE_MILES) -> dict:
    """Openings the window cannot see, by dating.

    Moving a date EARLIER — which is what replacing an OSHA bound with a
    stated opening does — pushes openings out of the front of the panel.
    Those ZCTAs are enabled at t=0, the risk-set builder left-truncates them,
    and the arm loses events it would have had on the later, wrong date. So
    "better dates" can mean "fewer events", and the comparison has to say by
    how many rather than let the reader assume it goes the other way.
    """
    dated = fac.dropna(subset=["open_year"])
    first_year = int(panel["year"].min())
    last_year = int(panel["year"].max())
    before = int((dated["open_year"] < first_year).sum())
    after = int((dated["open_year"] > last_year).sum())
    return {"dated_facilities": int(len(dated)),
            "opened_before_window": before,
            "opened_after_window": after,
            "inside_window": int(len(dated) - before - after),
            "window": [first_year, last_year],
            "radius_miles": miles}


def coverage_by_covariate(panel: pd.DataFrame) -> dict:
    """Non-null share of every candidate covariate, on the whole panel.

    This is the evidence the five-versus-three decision is taken on, and it
    is measured rather than carried over from the pilot frame.
    """
    return {c: round(100.0 * float(panel[c].notna().mean()), 1)
            for c in COVARIATES_5 if c in panel.columns}


def reproduces_disk(panel: pd.DataFrame, fac: pd.DataFrame,
                    geo: pd.DataFrame) -> dict:
    """The local target rebuild must match ``panel_expanded.parquet``.

    Same refusal ``catchment_band.reproduces_baseline`` makes: if the
    re-derived target disagrees with the delivered panel, every arm below is
    measuring a bug in this module.
    """
    ours = _enabled_at(panel[["zcta", "year", "quarter"]], fac, geo,
                       BASELINE_MILES)["enabled"].to_numpy(bool)
    theirs = panel["enabled"].fillna(False).to_numpy(bool)
    mismatch = int(np.not_equal(ours, theirs).sum())
    if mismatch:
        raise RuntimeError(
            f"the re-derived target disagrees with panel_expanded.parquet on "
            f"{mismatch:,} cells at {BASELINE_MILES} miles")
    return {"panel_enabled_cells": int(theirs.sum()),
            "recomputed_enabled_cells": int(ours.sum()),
            "mismatched_cells": 0}
