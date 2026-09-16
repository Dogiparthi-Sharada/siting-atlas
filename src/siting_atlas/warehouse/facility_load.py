"""Reading the facility panel: typing, the quarter index, and its provenance.

Split from ``facilities.py`` when that module crossed 300 lines. The seam is
real rather than arbitrary: everything here is about turning a hand-collected
CSV into typed rows and recording what had to be assumed on the way, and
nothing here knows anything about geometry, catchments or the panel.

Three facility frames exist and they are NOT interchangeable
------------------------------------------------------------
``FACILITY_FRAMES`` names them once so that no consumer has to retype a path
or guess a disposition. The differences are not cosmetic — each frame implies
a different target variable, and the audit of 2026-09-14 (§2.1) was
commissioned because three of them were live at once with nothing reconciling
them. Picking one is a decision, so it is spelled rather than defaulted
implicitly.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

from ..common import paths
from ..common.logging_setup import get_logger
from ..common.sentinels import flag_sentinels, flags_for
from .edits import EXCLUDE, REPORT, apply_operating_by, load_operating_bounds
from .facility_dedup import adjudicate

_log = get_logger("warehouse.facilities")

#: The facility frames that can set the target, by name: ``(filename,
#: disposition for the declared edit ``E_operating_by``)``.
#:
#: The disposition is part of the frame, not a caller's preference, and the
#: reason is already written down in two places. ``facility_load`` runs the
#: pilot in ``REPORT`` because excluding DS-032 removes Austin's only building
#: and moves published numbers. ``warehouse/national`` runs the national frame
#: in ``EXCLUDE`` because there the edit is what makes the file loadable at
#: all. The expanded frame inherits the national one's disposition for exactly
#: the same reason, and it is not a free choice: loaded in ``REPORT`` the
#: expanded file RAISES, because NAT-0011/NAT-0012, NAT-0025/NAT-0026 and
#: NAT-0078/NAT-0079 remain three contradicting pairs that no reliability
#: weight separates, and ``_refuse_unresolved`` stops the load rather than
#: manufacture a date. ``EXCLUDE`` falsifies one side of each pair with the
#: declared edit, which leaves nothing to adjudicate. Measured 2026-09-14.
FACILITY_FRAMES = {
    "pilot": ("facilities.csv", REPORT),
    "national": ("national_facilities.csv", EXCLUDE),
    "expanded": ("national_facilities_expanded.csv", EXCLUDE),
}

#: The frame every default build uses. ``panel.parquet``, the figures, the
#: choice report and the proposal are all on the pilot frame, so changing this
#: constant silently re-points published artefacts. Opt in per build instead —
#: ``python -m siting_atlas.warehouse.panel --facility-frame expanded`` — which
#: writes a differently named parquet and cannot overwrite the reference.
DEFAULT_FRAME = "pilot"

#: Escape hatch for callers that cannot pass an argument (a notebook, a shell
#: pipeline). Read once, at resolve time, and logged whenever it fires, so a
#: stray export can never change a panel without saying so.
FRAME_ENV = "SITING_ATLAS_FACILITY_FRAME"

#: Facility types that actually put a van on a residential street. Anything
#: else is logistics upstream of the last mile and does not set the target.
LAST_MILE_TYPES = {"DS", "SDC"}


def resolve_frame(frame: str | None = None) -> tuple[str, Path, str]:
    """Name, path and edit disposition for a facility frame.

    Precedence: the explicit argument, then ``$SITING_ATLAS_FACILITY_FRAME``,
    then :data:`DEFAULT_FRAME`. An unknown name is fatal — a typo that fell
    back to the default would build the pilot target under an expanded
    filename, which is the exact confusion this registry exists to end.
    """
    chosen = frame or os.environ.get(FRAME_ENV) or DEFAULT_FRAME
    if chosen not in FACILITY_FRAMES:
        raise ValueError(
            f"unknown facility frame {chosen!r}; known frames are "
            f"{', '.join(sorted(FACILITY_FRAMES))}. See "
            "docs/data/PANEL_EXPANSION.md sec. 11.")
    if frame is None and os.environ.get(FRAME_ENV):
        _log.warning("facility frame %r comes from $%s, not from an argument",
                     chosen, FRAME_ENV)
    filename, disposition = FACILITY_FRAMES[chosen]
    return chosen, paths.EXTERNAL / "facility_panel" / filename, disposition


def warehouse_flags(frame: str | None = None) -> dict[str, str]:
    """Quality flags this layer computes, keyed to the frame computing them.

    ``warehouse/flag_gate.py`` cannot discover these by scanning
    ``data/interim/``, because the facility panel never becomes an L1 parquet.
    Read off the sentinel registry rather than retyped, so adding a
    facility-panel sentinel cannot leave the gate behind.
    """
    _, path, _ = resolve_frame(frame)
    return dict.fromkeys(flags_for("facility_panel"), paths.rel(path))


#: The default frame's flags, for consumers that predate the registry.
WAREHOUSE_FLAGS = warehouse_flags(DEFAULT_FRAME)


def load_facilities(path=None, on_violation: str = REPORT) -> pd.DataFrame:
    """The frame alone. See :func:`load_with_edits` for the edit reports."""
    return load_with_edits(path, on_violation)[0]


def load_with_edits(path=None, on_violation: str = REPORT
                    ) -> tuple[pd.DataFrame, list[dict], list[dict]]:
    """Read the validated facility panel, typed and with a quarter index.

    ``zip`` is read as a string so leading zeros survive — the single most
    common way this file arrives damaged.

    ``on_violation`` is the disposition for a record that fails the declared
    cross-source edit ``E_operating_by`` (see ``warehouse/edits.py``). It
    defaults to ``REPORT`` — flag it, log it, leave it in place — for one
    stated reason and not because reporting is the safer default in general.

    The pilot file has exactly one violation, ``DS-032`` (Austin, claims
    2019Q3 against an OSHA inspection on 2019-03-15). Excluding it removes
    Austin's only building and moves numbers this project has already
    published: the ever-enabled ZCTA count, the enabled-cell count and the
    usable-event count. Moving a published number is the inspirator's call,
    so the edit reports and the decision is recorded rather than taken here.

    ``warehouse/national.py`` passes ``EXCLUDE``, because there the edit is
    what makes the file loadable at all and the records it drops are ones the
    source itself contradicts.

    Returns ``(frame, falsified, contradictions)``. The two reports are what
    the exclusion artefact is written from, so an exclusion is never only a
    log line.
    """
    path = path or (paths.EXTERNAL / "facility_panel" / "facilities.csv")
    frame = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    if frame.empty:
        raise ValueError(f"{paths.rel(path)} has a header but no data rows")

    frame["zcta"] = frame["zip"].str.strip().str.zfill(5)
    # `DataFrame.get(col, default)` returns the DEFAULT ITSELF, not a Series,
    # when the column is absent — so assigning its `.fillna(...)` blows up on
    # a plain string. Optional columns are therefore created explicitly.
    for col in ("latitude", "longitude", "open_year", "open_quarter",
                "close_year", "close_quarter"):
        frame[col] = (pd.to_numeric(frame[col], errors="coerce")
                      if col in frame.columns else pd.Series(
                          np.nan, index=frame.index, dtype=float))

    if "status" not in frame.columns:
        frame["status"] = "open"
    frame["status"] = frame["status"].fillna("open")
    # An unknown quarter defaults to Q1 rather than being dropped. Placing the
    # event at the start of the year is a stated convention; dropping the row
    # would silently shrink the event count, which is worse.
    #
    # The convention is not free, and until 2026-09-13 its cost was invisible:
    # 19 of the 43 delivered rows (44.2%) have no open_quarter, which puts
    # 35.47% of fitted events in Q1 against 25% expected under uniformity.
    # `outputs/metrics/hazard_report.json` has measured that artefact all
    # along and nothing could act on it, because the original NULL was
    # destroyed at load and no model could tell a convention from a date.
    #
    # Q1-by-convention is the SAME defect class as the ACS $250,001 top code:
    # Rahm & Do's missing values, a substitute standing in for a value nobody
    # reported, and Van den Broeck's erroneous inlier — plausible, in range,
    # and therefore invisible to every check this project runs. Both are
    # declared in one place, common/sentinels.py, and detected by one call.
    #
    # So: `open_quarter` keeps its NULL (the original value is retained, and
    # recovering it is reading this column), `open_q_index` keeps Q1 (the
    # operative value is unchanged, so no published number moves here), and
    # `open_quarter_imputed` carries the difference all the way to the panel.
    frame = flag_sentinels(frame, "facility_panel")
    frame["open_q_index"] = (frame["open_year"] * 4
                             + frame["open_quarter"].fillna(1) - 1)
    frame["close_q_index"] = np.where(
        frame["close_year"].notna(),
        frame["close_year"] * 4 + frame["close_quarter"].fillna(4) - 1,
        np.inf)

    # The declared edits run BEFORE adjudication, in that order for a reason.
    # E_operating_by falsifies one side of a contradicting pair outright, so
    # by the time the Sec. 7 reliability weights are consulted there is only
    # one admissible date left and nothing for them to tie on. Running the
    # weights first would leave three NaNs and refuse the load, which is what
    # happened before this edit existed.
    bounds = load_operating_bounds()
    frame, falsified = apply_operating_by(frame, bounds, on_violation,
                                          paths.rel(path))
    frame, contradictions = adjudicate(frame)
    _refuse_unresolved(contradictions, path)
    n_lastmile = frame["facility_type"].isin(LAST_MILE_TYPES).sum()
    _log.info("loaded %d facilities, %d last-mile (%s), %d imputed "
              "open_quarter, %d adjudicated duplicate group(s), %d falsified "
              "by E_operating_by", len(frame), n_lastmile,
              "/".join(sorted(LAST_MILE_TYPES)),
              int(frame["open_quarter_imputed"].sum()), len(contradictions),
              len(falsified))
    if n_lastmile == 0:
        _log.warning(
            "no DS or SDC rows — the target will be entirely FALSE. "
            "Fulfillment centres do not enable a ZIP for same-day service.")
    return frame, falsified, contradictions


def _refuse_unresolved(contradictions: list[dict], path) -> None:
    """Stop the load when two rows for one building disagree and nothing ranks
    them.

    The alternative is to invent a date, and Fellegi & Holt are explicit that
    inventing is the wrong branch: "one should, whenever possible, avoid
    'manufacturing' data instead of collecting it." A rule that picks the
    earlier date is not neutral — it is biased early on every pair — and the
    date being picked is the target variable.

    Deliberately fatal rather than a warning. ``facilities.attach`` catches
    this and leaves ``enabled`` NULL with an error naming
    ``ingest.external --check``, which is loud; a warning would be read once
    and the panel would ship with a manufactured event date in it.
    """
    blocked = [c for c in contradictions if c["unresolved"]]
    if not blocked:
        return
    detail = "\n".join(
        f"    {'/'.join(c['facility_ids'])}: {c['quarters_apart']} quarters "
        f"apart, both {', '.join(c['source_types']) or 'of unknown source'}"
        for c in blocked)
    raise ValueError(
        f"{paths.rel(path)} has {len(blocked)} contradicting facility "
        f"record(s) that no source-reliability ranking can separate:\n"
        f"{detail}\n"
        "Each is one building on two rows with two different opening dates, "
        "and the opening date is the target variable. Resolve it by "
        "collecting the date (a permit lookup), or by recording a "
        "source_type that ranks the two rows — not by a rule that picks one. "
        "See warehouse/facility_dedup.py.")


def resolve_coordinates(fac: pd.DataFrame,
                        zcta_geo: pd.DataFrame) -> pd.DataFrame:
    """Fill missing facility coordinates from their ZCTA centroid.

    Most press releases name a street, not a latitude. The centroid is within
    a couple of miles in an urban ZCTA, which is well inside the catchment
    radius, so it is a usable fallback rather than a reason to drop the row.
    """
    geo = zcta_geo.set_index("zcta")[["latitude", "longitude"]]
    filled = fac.copy()
    missing = filled["latitude"].isna() | filled["longitude"].isna()
    if missing.any():
        fallback = geo.reindex(filled.loc[missing, "zcta"])
        filled.loc[missing, "latitude"] = fallback["latitude"].to_numpy()
        filled.loc[missing, "longitude"] = fallback["longitude"].to_numpy()
        _log.info("filled %d facility coordinate(s) from the ZCTA centroid",
                  int(missing.sum()))

    unresolved = filled["latitude"].isna().sum()
    if unresolved:
        _log.warning("%d facility(ies) have no coordinate and no matching "
                     "ZCTA centroid; they cannot enable anything",
                     int(unresolved))
    return filled
