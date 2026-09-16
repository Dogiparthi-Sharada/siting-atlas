"""Turn a list of facilities into the panel's ``enabled`` target column.

This is the one piece of code standing between a delivered facility list and a
fitted model. It was written and tested before any data arrived; the pilot
file landed on 2026-09-13 and nothing here changed.

Which facility list — this is a choice, and it is made per build
----------------------------------------------------------------
Three frames now exist (``facility_load.FACILITY_FRAMES``) and they produce
three different target variables. Measured against ``dim_zcta`` and the
32-quarter panel keys on 2026-09-14, at the 15-mile DS catchment:

    frame      file                               rows  used  ZCTAs ever on
    pilot      facilities.csv                       43    43         1,257
    national   national_facilities.csv             104   100         2,713
    expanded   national_facilities_expanded.csv    700   543         8,937

``pilot`` is :data:`~.facility_load.DEFAULT_FRAME` and it is what
``data/processed/panel.parquet`` means. Every published figure, the choice
report and the proposal sit on it. The other two are opt-in — pass
``--facility-frame`` to ``warehouse.panel``, which writes a differently named
parquet so the reference cannot be overwritten by accident. The gap between
"rows" and "used" is itemised in :func:`attach`.

What the target actually means
------------------------------
``enabled`` is TRUE for a (ZCTA, quarter) when that ZIP-code area was inside
the catchment of an operating last-mile facility at that time. Three
decisions make that concrete, and each is a judgement worth arguing with
rather than a fact:

1. **Only delivery stations enable a ZIP.** A fulfillment centre is a
   regional node serving hundreds of miles; it does not put a van on a
   residential street. A sortation centre feeds delivery stations rather than
   doors. So DS and SDC set the target, and FC/SC/AMXL are carried for
   context but do not switch a ZIP on. Getting this wrong would make the
   model answer "where does Amazon warehouse things", not "where can you get
   a parcel the same day", which is a different question with a different
   answer.

2. **Catchment is a radius, not a polygon.** A real catchment is a drive-time
   isochrone shaped by roads. Without the routing matrix a radius is the
   honest approximation, and it is generous enough that the boundary cases
   are genuinely ambiguous rather than wrong.

3. **A facility switches its catchment on in its opening quarter and off in
   its closing quarter.** A ZIP served by two stations stays enabled until
   the last one closes.

Left-censoring
--------------
A facility that opened before the panel starts is not an event — but it does
mean its catchment was ALREADY enabled on day one. Dropping those rows would
tell the model those ZIPs were waiting to be switched on when they never
were, which biases every coefficient. They are kept, and the risk-set builder
in ``models/risk_set.py`` removes already-enabled units from the risk set.
"""

from __future__ import annotations

import pandas as pd

from ..common import paths
from ..common.logging_setup import get_logger
from ..common.trace import metric
from ..cost.daganzo import haversine_miles
from .edits import REPORT

# Re-exported: reading the file is a separate concern (see facility_load) but
# `warehouse.facilities` stays the one import path for the whole target build.
from .facility_load import (
    DEFAULT_FRAME,
    FACILITY_FRAMES,
    LAST_MILE_TYPES,
    WAREHOUSE_FLAGS,
    load_facilities,
    resolve_coordinates,
    resolve_frame,
    warehouse_flags,
)

__all__ = ["CATCHMENT_MILES", "DEFAULT_FRAME", "FACILITY_FRAMES",
           "LAST_MILE_TYPES", "WAREHOUSE_FLAGS", "attach", "build",
           "catchments", "enabled_flags", "load_facilities",
           "resolve_coordinates", "resolve_frame", "warehouse_flags"]

_log = get_logger("warehouse.facilities")

#: Catchment radius in miles, by facility type. A delivery station's service
#: area is commonly quoted at 20-30 minutes' drive; 15 miles straight-line is
#: the conservative reading of that in congested metros.
#:
#: ENGINEERING ESTIMATE. No published source was found for either figure, and
#: the "20-30 minutes" is itself an unsourced trade claim. The nearest
#: published catchments measure different facilities: Houde, Newberry and Seim
#: (2023) take Amazon's facility geography from MWPVL International and report
#: a 150-mile SORTATION catchment with a 25-mile FC-to-SC proximity rule, and
#: Holmes (2011) uses a 25-mile consumer choice radius for retail. None of
#: those is a last-mile delivery radius, so none of them settles 15.
#:
#: This parameter touches no cost figure at all, and it is still one of the
#: most consequential numbers in the project, because it sets the SAMPLE SIZE
#: for the causal stage. Measured against the delivered panel (2026-09-13):
#:
#:      5 mi ->    383 ZCTAs ever enabled        15 mi -> 1,257  (baseline)
#:     10 mi ->    882                           20 mi -> 1,593
#:                                               25 mi -> 1,819
#:
#: So 10 miles discards 30% of the treated units and 20 miles adds 27%,
#: against a panel that carries only 39 usable events. The hazard results
#: need a band across this radius, not a point estimate at 15.
#:
#: The error is not symmetric: a radius that is too LARGE labels untreated
#: ZIPs as treated, which attenuates every hazard coefficient toward zero.
#:
#: "SDC" is currently unreachable rather than wrong - every one of the 43 rows
#: in the delivered facilities.csv is a "DS", and so is every one of the 694
#: loadable rows in the expanded frame (measured 2026-09-14). It is untested,
#: not validated. See docs/data/PARAMETERS.md sec. 5 and sec. 6.21.
#:
#: The numbers above are the PILOT frame's. They have not been re-measured
#: across the radius band on the national or expanded frame, so quoting the
#: 4.7x sample-size swing alongside an expanded panel would be quoting one
#: frame's sensitivity at another frame's target.
CATCHMENT_MILES = {"DS": 15.0, "SDC": 10.0}


def catchments(fac: pd.DataFrame, zcta_geo: pd.DataFrame) -> pd.DataFrame:
    """Which ZCTAs each last-mile facility serves.

    Returns one row per (facility, zcta) pair with the quarter window the
    facility was operating.
    """
    live = fac[fac["facility_type"].isin(LAST_MILE_TYPES)].dropna(
        subset=["latitude", "longitude", "open_year"])
    if live.empty:
        return pd.DataFrame(columns=["zcta", "open_q_index",
                                     "open_quarter_imputed", "close_q_index"])
    if "open_quarter_imputed" not in live.columns:
        # Recomputed, never defaulted to False. A quality flag whose absent
        # case reads as "nothing was imputed here" is worse than no flag: it
        # is an assurance the code cannot give.
        live = live.assign(
            open_quarter_imputed=live["open_quarter"].isna()
            if "open_quarter" in live.columns else True)

    zlat = zcta_geo["latitude"].to_numpy(float)
    zlon = zcta_geo["longitude"].to_numpy(float)
    rows = []
    for _, f in live.iterrows():
        radius = CATCHMENT_MILES.get(f["facility_type"], 15.0)
        d = haversine_miles(zlat, zlon, f["latitude"], f["longitude"])
        hit = zcta_geo.loc[d <= radius, "zcta"]
        rows.append(pd.DataFrame({
            "zcta": hit.to_numpy(),
            "facility_id": f.get("facility_id", ""),
            "open_q_index": f["open_q_index"],
            # Travels with the date, not beside it: a consumer that has the
            # opening quarter and not the flag cannot tell a permit date from
            # a Q1 convention, which is the whole defect.
            "open_quarter_imputed": bool(f["open_quarter_imputed"]),
            "close_q_index": f["close_q_index"]}))

    out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    _log.info("%d facility-ZCTA catchment pairs from %d last-mile facilities",
              len(out), len(live))
    return out


def enabled_flags(panel_keys: pd.DataFrame, fac: pd.DataFrame,
                  zcta_geo: pd.DataFrame) -> pd.DataFrame:
    """The target column: one boolean per (zcta, year, quarter).

    ``panel_keys`` needs ``zcta``, ``year`` and ``quarter``. Returns the same
    keys plus ``enabled``, so the caller can join it straight onto the panel.
    """
    keys = panel_keys[["zcta", "year", "quarter"]].copy()
    keys["q_index"] = keys["year"] * 4 + keys["quarter"] - 1

    cover = catchments(fac, zcta_geo)
    if cover.empty:
        keys["enabled"] = False
        keys["open_quarter_imputed"] = False
        _log.warning("no catchments resolved; 'enabled' is entirely False")
        return keys.drop(columns="q_index")

    # A ZCTA is enabled from the earliest quarter any serving facility opened
    # until the latest quarter any of them was still operating. Taking the min
    # open and the max close is what lets two overlapping stations keep a ZIP
    # enabled through the closure of one of them.
    span = cover.groupby("zcta").agg(first_open=("open_q_index", "min"),
                                     last_close=("close_q_index", "max"))
    # The flag belongs to the facility that actually SET first_open, not to
    # any facility in the catchment: a ZIP switched on by a dated station and
    # later joined by an undated one has an observed switch-on date.
    setters = cover.merge(span["first_open"], on="zcta")
    setters = setters[setters["open_q_index"] == setters["first_open"]]
    span = span.join(setters.groupby("zcta")["open_quarter_imputed"].any())

    merged = keys.merge(span, on="zcta", how="left")
    merged["enabled"] = ((merged["q_index"] >= merged["first_open"])
                         & (merged["q_index"] <= merged["last_close"]))
    merged["enabled"] = merged["enabled"].fillna(False)
    # FALSE, not NULL, on a ZCTA no catchment covers: the predicate is "the
    # quarter this row was switched on is a Q1 convention", and a row that
    # was never switched on has no such quarter. That is a definite no, not
    # an unknown, so this is not the `enabled.fillna(False)` collapse.
    merged["open_quarter_imputed"] = (merged["open_quarter_imputed"]
                                      .fillna(False).astype(bool))

    rate = merged["enabled"].mean()
    _log.info("target built: %d of %d panel cells enabled (%.1f%%), "
              "%d distinct ZCTAs ever enabled, %d of those switched on by an "
              "imputed (Q1-by-convention) quarter",
              int(merged["enabled"].sum()), len(merged), rate * 100,
              int(merged.loc[merged["enabled"], "zcta"].nunique()),
              int(merged.loc[merged["enabled"]
                             & merged["open_quarter_imputed"],
                             "zcta"].nunique()))
    if rate == 0:
        _log.error("no panel cell is enabled — check that facility ZIPs "
                   "actually fall inside the pilot metros")
    return merged[["zcta", "year", "quarter", "enabled",
                   "open_quarter_imputed"]]


def build(panel_keys: pd.DataFrame, zcta_geo: pd.DataFrame,
          path=None, on_violation: str | None = None) -> pd.DataFrame:
    """Load, resolve and expand a facility frame into the target column.

    ``on_violation`` is the disposition for the declared edit
    ``E_operating_by``; ``None`` means the frame registry's, which is the only
    value that loads every frame (see ``facility_load.FACILITY_FRAMES``).
    """
    if on_violation is None:
        on_violation = REPORT if path is not None else resolve_frame()[2]
    fac = resolve_coordinates(load_facilities(path, on_violation), zcta_geo)
    return enabled_flags(panel_keys, fac, zcta_geo)


def attach(db, path=None, frame: str | None = None) -> int:
    """Populate ``enabled`` from a facility frame.

    Separated from the panel SQL because the target comes from a manually
    collected file rather than the warehouse.

    ``frame`` names one of ``facility_load.FACILITY_FRAMES`` and defaults to
    ``DEFAULT_FRAME`` (``pilot``, the 43-row hand-verified file that
    ``panel.parquet`` has always meant). ``path`` overrides it outright and
    keeps its historical disposition, ``REPORT``, so existing callers and
    tests are unaffected.

    What each frame loses on the way in, and why — measured 2026-09-14
    ------------------------------------------------------------------
    Nothing below is corrected or imputed. Every row that does not reach the
    catchment builder is dropped by a rule that already existed:

    ======== ===== ========== ====== ========= ====== ==============
    frame     rows  falsified  typed  no  year  no     sets a
                    by the     rows   (dropped  ZCTA   catchment
                    edit              by        centroid
                                      catchments)
    ======== ===== ========== ====== ========= ====== ==============
    pilot       43      0 [1]     43         0      0             43
    national   104      4        100         0      0            100
    expanded   700      6        694       144      7            543
    ======== ===== ========== ====== ========= ====== ==============

    [1] The pilot runs in ``REPORT``: its one violation, DS-032, is flagged
    and kept.

    The 144 undated expanded rows are the ones ``ingest/facility_check``
    rejects (``144 row(s) have a non-numeric open_year``; see
    ``PANEL_EXPANSION.md`` sec. 7.1). **They are loaded and then ignored by
    ``catchments``**, which already ``dropna``s on ``open_year`` — an
    undated facility has no quarter to switch its catchment on in, and
    inventing one would be the ``Q1-by-convention`` defect at a scale of 144
    rows rather than a stated convention on a known quarter. They are not
    deleted from the frame, so any consumer that wants their location still
    has it. The other 7 carry ``geo_status = postcode_not_a_zcta``: their
    postcode is not in the 2020 ZCTA relationship file, so
    ``resolve_coordinates`` has no centroid to fall back to and
    ``catchments`` cannot place them. That is 2 of the 9
    ``postcode_not_a_zcta`` rows being undated as well.

    Returns the number of enabled cells; 0 when the file is absent, which is
    a warning rather than an error. The panel must still build so that every
    stage below L4 keeps running.
    """
    if path is None:
        name, path, on_violation = resolve_frame(frame)
        _log.info("facility frame %r -> %s", name, paths.rel(path))
    else:
        on_violation = REPORT
    if not path.exists():
        _log.warning("no facility panel at %s; 'enabled' stays NULL and the "
                     "hazard model cannot be fitted", paths.rel(path))
        return 0

    try:
        keys = db.df("SELECT zcta, year, quarter FROM panel")
        geo = db.df("SELECT zcta, latitude, longitude FROM dim_zcta")
        flags = build(keys, geo, path, on_violation)
    except (ValueError, KeyError) as exc:
        # A malformed target file must not take the whole panel down — L0-L3
        # are still useful, and `ingest.external --check` is where the user
        # is told precisely what is wrong with the file.
        _log.error("facility panel present but unusable (%s); 'enabled' "
                   "stays NULL. Run ingest.external --check", exc)
        return 0

    db.register("target_flags", flags)
    db.execute("""
        CREATE OR REPLACE TEMP TABLE panel AS
        SELECT p.* REPLACE (
            COALESCE(t.enabled, FALSE) AS enabled,
            COALESCE(t.open_quarter_imputed, FALSE) AS open_quarter_imputed)
        FROM panel p
        LEFT JOIN target_flags t
               ON t.zcta = p.zcta AND t.year = p.year
              AND t.quarter = p.quarter
    """)
    n = db.scalar("SELECT COUNT(*) FROM panel WHERE enabled")
    metric("target_enabled_cells", n)
    _log.info("target attached: %d of %d panel cells enabled", n,
              db.scalar("SELECT COUNT(*) FROM panel"))
    return n
