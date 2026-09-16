"""Promote the national facility frame, and measure what it buys.

Why this module exists
----------------------
The model was fitted on 43 buildings in 10 metros because that is the only
frame the warehouse could load. ``national_facilities.csv`` has been sitting
beside it carrying 104 rows across 62 CBSAs, read by nothing in ``src/``, for
two reasons that are now one reason:

1. it needed national covariates at ZCTA grain, which is a real cost
   (``FACILITY_PANEL_PROVENANCE`` Sec. 16.3), and
2. three contradicting pairs made ``facility_load`` refuse it outright.

Only (2) was a blocker on loading the FACILITIES, and the declared edit
``E_operating_by`` clears it. This module is the seam: it loads the file under
that edit, writes the exclusions to an artefact, and reports the frame's size
against the power floor. It deliberately fits nothing.

**Corrected 2026-09-14.** This paragraph used to end "and joins nothing to the
panel". Joining is now possible -- ``warehouse/facility_load.FACILITY_FRAMES``
registers this file as the ``national`` frame and
``python -m siting_atlas.warehouse.panel --facility-frame national`` builds
``data/processed/panel_national.parquet`` from it (2,713 ZCTAs ever enabled
against the pilot's 1,257, measured 2026-09-14). Caution (1) is still unpaid:
the covariates in that panel are the same pinned national vintages either way,
so a bigger target does not buy a better covariate. This module still joins
nothing itself.

It also summarises the ``expanded`` frame on request -- ``--frame expanded``,
writing ``national_panel_expanded.json`` rather than overwriting this one.

What the numbers here are, and are not
--------------------------------------
``independent_episodes`` in ``models/diagnostics`` counts distinct
(metro, quarter) cells containing an event IN A RISK SET. There is no national
risk set, so the same definition is applied one layer up, to the facility
frame itself: distinct (CBSA, opening quarter) pairs among buildings that could
produce an event. It is the same quantity computed from the same definition on
a coarser object, and it is reported as a projection, not as a fitted result.

Three caveats survive the promotion and must travel with any quote of these
figures:

- **The dates are still OSHA upper bounds.** 100 of the 104 rows carry exactly
  the quarter of their building's earliest inspection. The measured lag from
  true opening to first inspection runs 4 to 345 months (Sec. 6.2). A bigger
  frame of upper bounds is a bigger frame of upper bounds.
- **Every coordinate is empty.** 0 of 104 rows here and 0 of 43 in the pilot
  carry a latitude or longitude, so ``resolve_coordinates`` falls back to the
  ZCTA centroid and every distance covariate inherits that error. Reported,
  not geocoded.
- **62 CBSAs at 1.6 buildings each** buys breadth at the cost of ever
  identifying a within-metro effect. The pilot frame is the denser one.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ..common import paths
from ..common.logging_setup import get_logger
from ..models.diagnostics import events_per_parameter
from .edits import EXCLUDE
from .facility_load import LAST_MILE_TYPES, load_with_edits, resolve_frame

_log = get_logger("warehouse.national")

NATIONAL_PATH = paths.EXTERNAL / "facility_panel" / "national_facilities.csv"
ARTEFACT = paths.METRICS / "national_panel.json"

#: The window of the feature panel the pilot model was fitted on. A building
#: outside it cannot contribute an event to anything fitted on that panel: an
#: opening at or before the first year is left-censored (its catchment was
#: already enabled on day one) and one after the last year has not happened
#: within the observation window.
PANEL_FIRST_YEAR = 2018
PANEL_LAST_YEAR = 2025

#: Parameters in the fitted pilot specification, so the two ratios are
#: comparable. Read from the emitted artefact when it is there rather than
#: retyped, because a hard-coded parameter count is wrong the first time the
#: specification changes.
FALLBACK_PARAMETERS = 5


def load_national(path=None) -> pd.DataFrame:
    """The national frame, with ``E_operating_by`` enforced.

    ``EXCLUDE`` here and ``REPORT`` on the pilot is the one asymmetry in this
    module and it is not a preference. Enforcing on the pilot would remove
    Austin's only building and move published numbers, which is the
    inspirator's decision; enforcing here removes four records that the source
    the file was derived from says cannot be right, and is what makes the file
    loadable at all.
    """
    return load_with_edits(path or NATIONAL_PATH, EXCLUDE)[0]


def _parameters() -> int:
    """The fitted specification's parameter count, from the artefact."""
    try:
        with open(paths.METRICS / "hazard_report.json", encoding="utf-8") as f:
            return int(json.load(f)["power"]["n_parameters"])
    except (OSError, KeyError, ValueError, TypeError):
        return FALLBACK_PARAMETERS


def first_in_metro(frame: pd.DataFrame) -> int:
    """Rows with no strictly earlier facility in their own CBSA.

    ``models/choice.build``'s prior-network rule, applied to a facility frame
    rather than inside a fit — the same move ``_episodes`` makes below, and
    for the same reason: the quantity is a property of the frame, and the
    frame is available long before a fit is.

    This is the denominator behind ``models/accessibility``'s finding that
    the line-haul covariate could not be tested. An UNDATED row can never
    have a prior under this rule, so it counts as first, which is why adding
    undated facilities raises this number rather than lowering it.
    """
    year = pd.to_numeric(frame.get("open_year"), errors="coerce")
    title = frame["cbsa_title"].astype(str)
    return int(sum(1 for i in frame.index
                   if not ((title == title[i]) & (year < year[i])).any()))


def _episodes(frame: pd.DataFrame) -> int:
    """Distinct (CBSA, opening quarter) cells — the conservative bound."""
    if frame.empty:
        return 0
    key = frame["cbsa_title"] if "cbsa_title" in frame.columns \
        else frame["state"]
    return int(len(pd.DataFrame({"m": key.astype(str),
                                 "q": frame["open_q_index"]})
                   .drop_duplicates()))


def artefact_path(frame: str) -> Path:
    """Where a frame's summary goes. ``national`` keeps :data:`ARTEFACT`.

    Same guard as ``warehouse/panel.panel_path``: no argument makes an
    expanded summary land on top of the national one.
    """
    if frame == "national":
        return ARTEFACT
    return ARTEFACT.with_name(f"{ARTEFACT.stem}_{frame}{ARTEFACT.suffix}")


def summarise(out_path=None, path=None, frame: str | None = None) -> dict:
    """Load, measure and write the artefact. Returns what it wrote.

    ``frame`` names a facility frame; ``path`` overrides it. Both default to
    the 104-row national file, which is what ``national_panel.json`` has
    always meant.
    """
    if path is None:
        frame = frame or "national"
        path = resolve_frame(frame)[1]
        out_path = out_path or artefact_path(frame)
    path = path or NATIONAL_PATH
    raw = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    frame, falsified, contradictions = load_with_edits(path, EXCLUDE)

    live = frame[frame["facility_type"].isin(LAST_MILE_TYPES)
                 & frame["open_q_index"].notna()]
    year = (live["open_q_index"] // 4).astype(int)
    in_window = live[(year >= PANEL_FIRST_YEAR) & (year <= PANEL_LAST_YEAR)]
    # An opening in the panel's FIRST year is left-censored, not an event.
    events = in_window[(in_window["open_q_index"] // 4) > PANEL_FIRST_YEAR]

    n_params = _parameters()
    report = {
        "source": paths.rel(path),
        "rows_in_file": int(len(raw)),
        "buildings": int(len(frame)),
        "cbsas": int(frame["cbsa_title"].nunique())
        if "cbsa_title" in frame.columns else None,
        "states": int(frame["state"].nunique()),
        "coordinates_present": int(frame["latitude"].notna().sum()),
        # Counted, never retyped. The literal "0 of 104" survived the 700-row
        # expansion unchanged and was still being read as a fact about
        # whichever file the module had just loaded.
        "coordinate_note": (
            f"{int(frame['latitude'].notna().sum())} of {len(raw)} rows "
            f"carry a coordinate, as in the 43-row pilot file. "
            "resolve_coordinates falls back to the ZCTA centroid, so every "
            "distance covariate is known only to that precision. Not "
            "geocoded here; see STATUS.md section 3 blocker 4."),
        "excluded": falsified,
        "exclusion_note": (
            "Each record below fails the declared edit E_operating_by: it "
            "claims an opening strictly after the date an OSHA inspection "
            "proves the establishment was already operating. The CSV is "
            "untouched and claimed_open preserves the rejected value, so the "
            "exclusion is reversible from this file alone."),
        "contradictions_remaining": [c for c in contradictions
                                     if c["unresolved"]],
        "in_panel_window": {
            "first_year": PANEL_FIRST_YEAR,
            "last_year": PANEL_LAST_YEAR,
            "buildings": int(len(in_window)),
            "cbsas": int(in_window["cbsa_title"].nunique())
            if "cbsa_title" in in_window.columns else None,
            "events": int(len(events)),
            "independent_episodes": _episodes(events),
            "left_censored": int((in_window["open_q_index"] // 4
                                  == PANEL_FIRST_YEAR).sum()),
            "outside_window": int(len(live) - len(in_window)),
        },
        "power": events_per_parameter(
            n_events=int(len(events)), n_parameters=n_params,
            n_episodes=_episodes(events), n_facilities=int(len(events))),
        "note": (
            "Projected, not fitted. The episode count applies "
            "models.diagnostics.independent_episodes' definition to the "
            "facility frame rather than to a risk set, because no national "
            "risk set exists. For the same reason power.n_events_zcta here "
            "counts BUILDINGS, not ZCTAs, so power.events_per_parameter_"
            "nominal is not the inflated figure that field carries in "
            "hazard_report.json -- it equals the optimistic bound by "
            "construction and should be ignored. The dates remain OSHA upper "
            "bounds with a measured 4-345 month lag to the true opening."),
    }

    out_path = out_path or ARTEFACT
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=False)
        fh.write("\n")

    window = report["in_panel_window"]
    _log.info("national frame: %d rows -> %d buildings across %d CBSAs "
              "(%d excluded by E_operating_by); %d events in %d CBSAs within "
              "%d-%d, %d independent episodes, %.1f per parameter against a "
              "floor of %.0f",
              report["rows_in_file"], report["buildings"], report["cbsas"],
              len(falsified), window["events"], window["cbsas"],
              PANEL_FIRST_YEAR, PANEL_LAST_YEAR,
              window["independent_episodes"],
              report["power"]["events_per_parameter_optimistic"],
              report["power"]["floor"])
    return report


def main() -> int:
    import argparse

    from ..common.context import init_run
    from ..common.logging_setup import configure

    ap = argparse.ArgumentParser(description="summarise a facility frame")
    ap.add_argument("--frame", default="national",
                    choices=("national", "expanded"),
                    help="which frame to measure (default national; "
                         "'expanded' writes national_panel_expanded.json)")
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()
    report = summarise(frame=args.frame)
    window = report["in_panel_window"]
    print(f"\n  {report['source']}")
    print(f"    {report['rows_in_file']} rows -> {report['buildings']} "
          f"buildings, {report['cbsas']} CBSAs, {report['states']} states")
    print(f"    {len(report['excluded'])} excluded by E_operating_by: "
          f"{', '.join(e['facility_id'] for e in report['excluded'])}")
    print(f"    within {window['first_year']}-{window['last_year']}: "
          f"{window['events']} events, {window['cbsas']} CBSAs, "
          f"{window['independent_episodes']} independent episodes")
    print(f"    events per parameter "
          f"{report['power']['events_per_parameter_effective']}"
          f" .. {report['power']['events_per_parameter_optimistic']} "
          f"(floor {report['power']['floor']:.0f}, "
          f"{'MET' if report['power']['meets_floor'] else 'NOT MET'})")
    print(f"    coordinates present: {report['coordinates_present']}\n")
    print(f"  -> {paths.rel(artefact_path(args.frame))}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
