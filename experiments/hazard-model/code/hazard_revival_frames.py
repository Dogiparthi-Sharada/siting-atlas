"""Frames for the hazard revival: the expanded panel, dated two ways.

The retired hazard model ran on 43 pilot facilities and 39 events, dated by
OSHA "operating by" upper bounds. Two of those handicaps have been removed:
``panel_expanded.parquet`` carries 687 loadable facilities, and 545 of them
carry an opening date that MWPVL states rather than an OSHA bound infers.

This module builds the arms. It does not fit anything.

What "old dates" can and cannot mean here
-----------------------------------------
The control the revival needs is "the same panel, dated the old way", so
that a change in the numbers can be attributed to the DATES rather than to
the extra events. That control is weaker than it sounds and the reason is
worth stating before any number is quoted.

An OSHA bound exists only where an inspection happened. Of the 687 loadable
expanded facilities, **139** match an OSHA building at all (100 of them are
the national rows, whose dates already ARE the bound); the other 548 have no
bound to fall back on. So:

    NEW   545 dated facilities, MWPVL dates where MWPVL has one
    OLD   139 dated facilities, every date replaced by its OSHA bound,
          the rest DROPPED -- never imputed, per the standing rule
    PAIR  130 facilities dated under both, run twice. Only 30 of those 130
          actually move, because the 100 national rows were derived from
          the bound in the first place.

``PAIR`` is the only arm where facility membership is held constant, so it
is the only clean date contrast in the data — and it is a 30-facility
contrast. ``OLD`` answers a different and still useful question: what an
OSHA-only national panel would have produced.

Nothing here corrects or imputes a value. A facility with no MWPVL date
keeps whatever date its own row carries (which for the 104 national rows is
the OSHA bound); a facility with no date at all never reaches
``catchments`` and is counted as lost.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..common import paths
from ..common.logging_setup import get_logger
from ..common.metros import REGISTRY
from ..warehouse import facility_load as fl
from ..warehouse.catchment_band import BASELINE_MILES
from ..warehouse.catchment_band import enabled_at as _enabled_at

_log = get_logger("models.hazard_revival_frames")

#: The expansion's own panel. ``paths.PANEL`` is the 43-facility pilot frame
#: and reading it here is exactly the mistake the revival exists to fix.
EXPANDED_PANEL = paths.ROOT / "data" / "processed" / "panel_expanded.parquet"

#: The three the retired run used. ``hazard_report.json`` fitted these.
COVARIATES_3 = ("households", "median_household_income", "establishments")

#: The two ``panel_source.REAL_COVARIATES`` dropped when it was cut from five
#: to three. The original tuple predates version control, so this is a
#: reconstruction and not a recovered literal: ``panel_source``'s docstring
#: names ``rent_index_yoy_pct`` as one of the casualties, and the panel holds
#: exactly two "rates of change" columns (``warehouse/panel.py`` docstring),
#: which are these. Both are stated as such wherever they are reported.
COVARIATES_ADDED = ("rent_index_yoy_pct", "permits_yoy_pct")
COVARIATES_5 = COVARIATES_3 + COVARIATES_ADDED
#: The middle arm. ``permits_yoy_pct`` is 75% covered at national scope and
#: ``rent_index_yoy_pct`` is 19%; see ``covariate_decision``.
COVARIATES_4 = COVARIATES_3 + ("permits_yoy_pct",)


@dataclass(frozen=True)
class ArmFrame:
    """A scoped panel with its target already set, plus how it got there."""

    frame: pd.DataFrame
    covariates: tuple[str, ...]
    detail: dict


def load_expanded_facilities(geo: pd.DataFrame) -> pd.DataFrame:
    """The 687 loadable expanded facilities, coordinates resolved.

    ``EXCLUDE`` is the registry's disposition for this frame and is not a
    choice made here: loaded in ``REPORT`` the file raises on three
    contradicting pairs. Six rows fail ``E_operating_by`` and are dropped by
    that edit before this function returns, which is why 693 rows in the CSV
    become 687 here.
    """
    _, path, disposition = fl.resolve_frame("expanded")
    fac = fl.load_facilities(path, disposition)
    return fl.resolve_coordinates(fac, geo)


def redate_to_osha_bound(fac: pd.DataFrame) -> pd.DataFrame:
    """Every facility re-dated to the quarter of its OSHA bound.

    Facilities with no OSHA match are DROPPED rather than given a date. The
    bound is an exact inspection date, so ``open_quarter`` is observed and
    ``open_quarter_imputed`` is False — which is the one respect in which
    this arm is cleaner than the frame's own dates.
    """
    bound = pd.to_datetime(fac["osha_operating_by"], errors="coerce")
    out = fac.loc[bound.notna()].copy()
    stamp = bound.loc[out.index]
    out["open_year"] = stamp.dt.year.astype(float)
    out["open_quarter"] = stamp.dt.quarter.astype(float)
    out["open_q_index"] = out["open_year"] * 4 + out["open_quarter"] - 1
    out["open_quarter_imputed"] = False
    _log.info("OSHA-bound arm: %d of %d facilities carry a bound; %d dropped "
              "for want of one (no date is invented)",
              len(out), len(fac), len(fac) - len(out))
    return out


def scoped_frame(panel: pd.DataFrame, fac: pd.DataFrame, geo: pd.DataFrame,
                 covariates: tuple[str, ...],
                 miles: float = BASELINE_MILES) -> ArmFrame:
    """Set the target from ``fac``, cut to scope, drop incomplete rows.

    SCOPE is the CBSAs this arm's own facilities reach, minus the two metros
    ``common.metros`` declares held out. ``panel_source.restrict_to_scope``
    hard-codes the nine pilot metros, which would throw away most of the
    expansion, so the same rule is applied at national grain instead: a ZCTA
    is in the choice set if some station in its metro was sited during the
    window, and is otherwise never considered.

    MISSINGNESS is dropped, never imputed, and the cost is recorded in
    ``detail`` because the five-covariate arm pays most of it.
    """
    keys = panel[["zcta", "year", "quarter"]]
    flags = _enabled_at(keys, fac, geo, miles)
    frame = panel.drop(columns=["enabled"]).merge(
        flags, on=["zcta", "year", "quarter"], how="left")

    on = frame["enabled"].fillna(False).to_numpy(bool)
    reached = set(frame.loc[on, "cbsa_code"].dropna().astype(str))
    held = set(REGISTRY.heldout_codes)
    scoped = frame[frame["cbsa_code"].astype(str).isin(reached - held)]
    present = tuple(c for c in covariates if c in scoped.columns)
    complete = scoped.dropna(subset=list(present)) if present else scoped

    detail = {
        "radius_miles": miles,
        "enabled_cells_national": int(on.sum()),
        "zctas_ever_enabled_national": int(frame.loc[on, "zcta"].nunique()),
        "cbsas_reached": len(reached),
        "cbsas_in_scope": len(reached - held),
        "cbsas_held_out": sorted(held & reached),
        "rows_in_scope": int(len(scoped)),
        "rows_after_covariate_dropna": int(len(complete)),
        "pct_rows_lost_to_missingness": round(
            100.0 * (1 - len(complete) / max(len(scoped), 1)), 1),
        "units_in_scope": int(scoped["zcta"].nunique()),
        "units_complete": int(complete["zcta"].nunique()),
        "covariates": list(present),
    }
    _log.info("arm scope: %d CBSAs, %d rows -> %d after dropping %s gaps",
              detail["cbsas_in_scope"], detail["rows_in_scope"],
              detail["rows_after_covariate_dropna"], list(present))
    return ArmFrame(frame=complete.copy(), covariates=present, detail=detail)


def heldout_frame(panel: pd.DataFrame, fac: pd.DataFrame, geo: pd.DataFrame,
                  covariates: tuple[str, ...],
                  miles: float = BASELINE_MILES) -> pd.DataFrame:
    """Phoenix and Boise, which no fit is allowed to see.

    The retired run's transfer check was a smoke test because those two
    metros held two dated stations between them. The expanded frame changes
    that arithmetic; how much is reported rather than assumed.
    """
    keys = panel[["zcta", "year", "quarter"]]
    flags = _enabled_at(keys, fac, geo, miles)
    frame = panel.drop(columns=["enabled"]).merge(
        flags, on=["zcta", "year", "quarter"], how="left")
    held = frame[frame["cbsa_code"].astype(str).isin(
        set(REGISTRY.heldout_codes))]
    present = [c for c in covariates if c in held.columns]
    return held.dropna(subset=present).copy() if present else held.copy()
