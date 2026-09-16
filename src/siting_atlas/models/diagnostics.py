"""What the real facility panel will not support, measured rather than felt.

Everything here exists because the delivered target is small and contaminated
in specific, nameable ways, and because each of those ways produces a number
that looks respectable if it is quoted on its own. The module's job is to put
the disqualifying figure next to the flattering one in the same report.

Counting only. Nothing here refits anything — the checks that re-estimate
the model live in ``sensitivities.py``, and the boundary is worth keeping
because a counter can only be wrong about the data in front of it.

    independent_episodes    a station flips a whole catchment at once, so the
                            ZCTA event count is not a count of decisions
    usable_facilities       the other end of that bracket, audited buildings
    events_per_parameter    both bounds against the conventional floor
    events_by_metro         a metro contributing nothing must stay visible
    event_timing            the dates have no quarter, so every event lands
                            in Q1 and three quarters of the risk set is a
                            structural zero
    CONTAMINATION           the OSHA upper-bound problem, with the lag to
                            first inspection measured rather than asserted
"""

from __future__ import annotations

import pandas as pd

from ..common.logging_setup import get_logger
from .risk_set import EVENT_COL, TIME_COL

_log = get_logger("models.diagnostics")

#: Conventional minimum number of events per estimated parameter for a
#: binary-outcome regression. Below it the coefficients are driven by a
#: handful of observations and the standard errors understate that.
EPP_FLOOR = 10.0


def independent_episodes(risk: pd.DataFrame,
                         cluster_col: str = "cbsa_code") -> int:
    """How many separate siting decisions the events actually represent.

    A delivery station flips every ZCTA inside its catchment in one quarter,
    so a hundred ZCTA-level events can be one decision. Counting distinct
    (metro, quarter) cells that contain an event is the coarsest honest
    proxy available from the risk set alone: it merges two stations opened
    in the same metro in the same quarter into one episode, which errs
    toward the smaller number, and the smaller number is the one a power
    calculation should be run on.
    """
    if cluster_col not in risk.columns:
        return int(risk.loc[risk[EVENT_COL] == 1, TIME_COL].nunique())
    fired = risk.loc[risk[EVENT_COL] == 1, [cluster_col, TIME_COL]]
    return int(len(fired.drop_duplicates()))


def events_by_metro(risk: pd.DataFrame,
                    cluster_col: str = "cbsa_code") -> list[dict]:
    """Units at risk and events, one row per fitting metro.

    Reported because a metro that contributes nothing has to be visible.
    Nashville is in the fitting sample and has zero events — its five OSHA
    addresses are all fulfilment centres, which the target builder correctly
    refuses to count as last-mile. Averaged into a national figure that
    disappears; listed here it is a statement about the sample, namely that
    the covariate contrasts are being identified off seven metros and not
    eight.
    """
    if cluster_col not in risk.columns:
        return []
    grouped = risk.groupby(cluster_col)
    out = [{"cbsa_code": str(code),
            "units_at_risk": int(g["zcta"].nunique()),
            "rows": int(len(g)),
            "events": int(g[EVENT_COL].sum())}
           for code, g in grouped]
    out.sort(key=lambda r: -r["events"])
    silent = [r["cbsa_code"] for r in out if r["events"] == 0]
    if silent:
        _log.warning("%d fitting metro(s) contribute no event at all (%s); "
                     "every covariate contrast comes from the others",
                     len(silent), ", ".join(silent))
    return out


def usable_facilities(scoped_panel: pd.DataFrame) -> int | None:
    """Audited buildings that could have produced an event in this sample.

    The other end of the bracket from :func:`independent_episodes`, which
    merges every station a metro opened in one year into a single draw —
    Seattle opened four in 2023 and they count once there.

    Pass the SCOPED PANEL, not a risk set and not a split, for two reasons
    that each cost about a third of the count:

    A station's own ZIP is one ZCTA out of the ninety its fifteen-mile
    catchment covers, so a split's ZCTA list drops stations whose own ZIP
    was randomised elsewhere while their catchment sits in training.

    A risk set has already removed the left-truncated ZCTAs, and a station
    sitting in a ZIP that some earlier station had already enabled is
    exactly such a ZCTA — so the newer station becomes unmappable and
    vanishes from a count it belongs in. Between them these two took 38
    buildings down to 29 and briefly made the "optimistic" bound smaller
    than the conservative one.

    Openings at or before the panel's first year are excluded. Those are
    left-censored — their catchments were already enabled on day one — so
    they contribute no event to estimate anything from.

    Read from the target file rather than hard-coded, because a hard-coded
    sample size is wrong the first time anyone corrects a row. ``None`` when
    the file is unreadable; the episode count stands on its own.
    """
    try:
        from ..warehouse.facilities import LAST_MILE_TYPES, load_facilities
        fac = load_facilities()
    except (OSError, ValueError, KeyError) as exc:
        _log.warning("cannot count facilities for the power check (%s)", exc)
        return None

    first_year = (int(scoped_panel["year"].min())
                  if "year" in scoped_panel else 0)
    live = fac[fac["facility_type"].isin(LAST_MILE_TYPES)
               & (fac["open_year"] > first_year)]
    if "zcta" in scoped_panel:
        live = live[live["zcta"].isin(set(scoped_panel["zcta"]))]
    return int(len(live))


def events_per_parameter(n_events: int, n_parameters: int, n_episodes: int,
                         n_facilities: int | None = None) -> dict:
    """Three counts, because only the last two bound anything real.

    The nominal ratio divides ZCTA-level events by parameters and will be in
    the hundreds. It is the number that makes this model look adequately
    powered and it is meaningless: every ZCTA inside one delivery station's
    catchment enables in the same quarter, so those events are one draw.

    The truth is bracketed rather than known. The metro-quarter episode
    count is a LOWER bound on independent decisions — it merges four Seattle
    stations opened in the same year into one. The usable-facility count is
    an UPPER bound — four stations opened by one metro in one year are
    plausibly one capacity programme, not four decisions. Both bounds are
    reported and the verdict is taken on the optimistic one, so a failure to
    meet the floor cannot be blamed on the conservative proxy.
    """
    def ratio(n):
        return n / n_parameters if n_parameters else float("nan")

    best = max(n_episodes, n_facilities or 0)
    return {
        "n_events_zcta": int(n_events),
        "n_independent_episodes": int(n_episodes),
        "n_usable_facilities": n_facilities,
        "n_parameters": int(n_parameters),
        "events_per_parameter_nominal": round(ratio(n_events), 2),
        "events_per_parameter_effective": round(ratio(n_episodes), 2),
        "events_per_parameter_optimistic": round(ratio(best), 2),
        "floor": EPP_FLOOR,
        # Judged on the OPTIMISTIC bound deliberately. If even the most
        # generous reading of the sample size is below the floor, no
        # argument about the proxy can rescue the specification.
        "meets_floor": bool(ratio(best) >= EPP_FLOOR),
        "note": (
            "The nominal ratio counts ZCTAs and is not evidence of power. "
            "Independent decisions lie between the metro-quarter episode "
            "count (lower bound, merges same-year openings in one metro) "
            "and the usable-facility count (upper bound). The verdict is "
            "taken on the upper bound."),
    }


def event_timing(risk: pd.DataFrame) -> dict:
    """Where in the calendar the events sit — and whether that is an artefact.

    A facility row with no ``open_quarter`` is placed in Q1 by
    ``warehouse.facilities``, by its stated convention. When *every* row is
    undated that way the consequence is not cosmetic: no event can occur in
    Q2, Q3 or Q4, so three quarters of every row in the risk set is a
    non-event by construction rather than by observation. A quarterly hazard
    fitted on it is being asked to explain a periodicity that is an artefact
    of a missing column, and any baseline flexible enough to see the
    periodicity (``dummies``) separates perfectly and blows up.

    Everything below is **measured from the risk set rather than asserted**.
    An earlier version hardcoded the sentence "open_quarter is empty for all
    49 facilities"; the panel has since been rebuilt with real source months
    on part of it, and the emitted JSON went on claiming a defect the data
    no longer had. A diagnostic that states a fixed conclusion is not a
    diagnostic.
    """
    events = risk.loc[risk[EVENT_COL] == 1]
    has_q = "quarter" in risk
    by_quarter = events.groupby("quarter").size() if has_q \
        else pd.Series(dtype=int)
    share_q1 = float(by_quarter.get(1, 0) / len(events)) if len(events) \
        else float("nan")
    # A row is structurally eventless when its quarter-of-year contains no
    # event anywhere in the sample: the model cannot be asked to explain it,
    # because nothing in that calendar slot ever happens. Counting "not Q1"
    # would be the same number only in the all-undated case, and plain wrong
    # once some facilities carry a real month.
    if has_q:
        live = {int(q) for q, n in by_quarter.items() if n > 0}
        eventless = round(float((~risk["quarter"].isin(live)).mean()), 4)
    else:
        eventless = None
    n_live = len(by_quarter[by_quarter > 0]) if has_q else 0
    if n_live <= 1:
        cause = (
            f"Every event falls in a single quarter of the year, because "
            f"open_quarter is absent on the facilities that drive them and "
            f"warehouse.facilities dates an undated opening to Q1. "
            f"{eventless:.0%} of risk-set rows are therefore structural "
            f"zeros, and the quarterly grain is finer than the target's "
            f"resolution.")
    else:
        cause = (
            f"Events fall in {n_live} of the 4 quarters of the year, so the "
            f"Q1 pile-up that made the quarterly grain meaningless is no "
            f"longer total. Rows whose open_quarter is still blank are "
            f"dated to Q1 by convention, which is why Q1 remains the "
            f"largest bucket at {share_q1:.0%} of events — read the "
            f"quarter-of-year distribution as partly a coverage artefact, "
            f"not as seasonality.")
    return {
        "distinct_event_times": int(events[TIME_COL].nunique()),
        "events_by_quarter_of_year": {int(k): int(v)
                                      for k, v in by_quarter.items()},
        "share_in_q1": round(share_q1, 4),
        "rows_structurally_eventless": eventless,
        "cause": cause,
    }

#: as an event time.
BOUND_LAG_MONTHS = (4, 13, 57, 69, 345)

#: Stated once, attached to every artefact that could be read as a temporal
#: claim, so it cannot be separated from the number it qualifies.
CONTAMINATION = (
    "Most facility dates are 'operating by' UPPER BOUNDS derived from OSHA "
    "inspection records, not opening dates. An inspection occurs at an "
    "already-operating site, so recently inspected sites are dated as "
    "recently opened; 2023 is the largest cohort and is far more likely to "
    "reflect inspection activity than construction. The looseness has been "
    f"measured on the five addresses that also appear in MWPVL's 2012 table "
    f"with real opening months: the bound held 5 of 5 times, but the lag "
    f"between opening and first inspection was {BOUND_LAG_MONTHS} months — "
    "one site opened in 1997 and was first inspected in 2026. The dates are "
    "therefore valid RIGHT-hand endpoints of a censoring interval and are "
    "not event times. Any result that depends on WHEN an event happened "
    "inherits that, which is why the temporal split is reported as secondary "
    "and the unit-clustered split is the primary evidence. The specification "
    "this target actually calls for is interval censoring, which the current "
    "risk-set builder does not implement."
)
