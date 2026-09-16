"""Turning a dense ZCTA-quarter panel into a discrete-time risk set.

The one rule
------------
A unit contributes rows for every quarter it was *at risk of the event*, and
NOT ONE ROW MORE. A ZCTA that gets a facility in 2022Q3 is at risk from the
start of the panel through 2022Q3, and after that it is out of the sample
forever. It cannot be enabled twice.

Why this is the silent error and not a loud one
-----------------------------------------------
The panel is dense by construction — every ZCTA has all 32 quarters whether
anything happened or not. Feed it straight into a binary regression and the
code runs, the coefficients print, the standard errors look tight, and every
number is wrong. Consider a ZCTA enabled in 2018Q2:

    correct risk set      2 rows, outcomes 0, 1                 -> 1 event
    dense panel as-is    32 rows, outcomes 0, 1, 0, 0, ... 0    -> 1 event
                                                                   and 30
                                                                   fake
                                                                   non-events

Those thirty rows say "this ZCTA was available to be chosen and was not
chosen", thirty times, about the most attractive ZCTA in the sample. The
estimator concludes that whatever made it attractive predicts *not* being
chosen. The bias is toward zero and can flip a sign, and nothing in the
output complains: no NaN, no convergence warning, no missing data. It is the
classic duration-model error precisely because it never announces itself.

The everyday version: you are measuring how long lightbulbs last, and you
keep writing "still working" in the log for weeks after a bulb has burnt out
and been thrown away.

Two encodings, one risk set
---------------------------
The facility panel can arrive encoded either way and both are reasonable:

    STATE flag   enabled = True from the opening quarter onwards
    EVENT flag   enabled = True only in the opening quarter

Taking the FIRST true row as the event and discarding everything after it
gives the identical risk set under both encodings, so the modelling layer
does not have to care which convention the panel builder chose. That
equivalence is asserted in the tests rather than hoped for.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common.logging_setup import get_logger
from .truthy import as_boolean

_log = get_logger("models.risk_set")

ID_COL = "zcta"
EVENT_COL = "event"
TIME_COL = "t"


class TargetUnpopulatedError(ValueError):
    """Raised when the outcome column carries no observed events.

    A distinct exception type because the caller's correct response is not
    "fix the call" but "the facility panel has not arrived yet, fall back to
    the labelled synthetic fixture" — and that decision should be taken on a
    type, not by matching on a message string.
    """


def quarter_index(year, quarter, base_year: int | None = None) -> pd.Series:
    """Quarters elapsed since the first quarter in the data, 0-based.

    Calendar year and quarter are two columns and duration models need one
    clock. Keeping the origin at the panel's own first quarter (rather than
    at year 0) keeps the numbers small, which matters once they are cubed
    into a spline basis.

    Two details that look like pedantry and are not:

    The ORIGIN is the earliest year-quarter pair, not the earliest year. A
    panel opening in 2018Q3 has no 2018Q1 and no 2018Q2, so ``(year - 2018)
    * 4 + (quarter - 1)`` starts the clock at 2, asserting two quarters of
    exposure that were never observed. The spline knots then sit on a grid
    beginning at 2 and the reported "t=0 hazard" describes a quarter outside
    the data.

    The caller's INDEX is preserved. Wrapping the inputs in a fresh
    ``pd.Series`` hands back a RangeIndex, so ``frame["t"] = quarter_index(
    frame["year"], frame["quarter"])`` aligns on labels that do not match and
    fills the whole column with NaN. On a frame that has been filtered or
    concatenated — which is every frame here — that is silent, and the
    failure surfaces much later as a design matrix full of missing time.
    """
    year_s = pd.Series(np.asarray(year, dtype="int64"))
    quarter_s = pd.Series(np.asarray(quarter, dtype="int64"))
    index = year.index if isinstance(year, pd.Series) else year_s.index
    year_s.index, quarter_s.index = index, index

    absolute = year_s * 4 + (quarter_s - 1)
    origin = int(absolute.min()) if base_year is None else base_year * 4
    return absolute - origin


def build_risk_set(panel: pd.DataFrame, *, id_col: str = ID_COL,
                   year_col: str = "year", quarter_col: str = "quarter",
                   enabled_col: str = "enabled",
                   drop_left_truncated: bool = True) -> pd.DataFrame:
    """Dense panel in, risk set out.

    Adds two columns and removes rows:

        ``t``      quarters since the start of the panel
        ``event``  1 in the quarter the unit enabled, 0 otherwise

    Every row after a unit's first event is dropped. Units that never enable
    are right-censored and keep all of their rows, which is correct: "it had
    not happened by the end of the window" is information, and discarding
    censored units is how you end up estimating the hazard among the treated.
    """
    for col in (id_col, year_col, quarter_col, enabled_col):
        if col not in panel.columns:
            raise KeyError(
                f"panel is missing {col!r}; build_risk_set needs id, year, "
                f"quarter and the outcome")

    frame = panel.copy()
    frame[TIME_COL] = quarter_index(frame[year_col],
                                    frame[quarter_col]).to_numpy()

    # NULL is not False. The panel ships the target as an all-NULL typed
    # column before the facility data lands, and fillna(False) there would
    # hand the estimator a sample in which nothing ever happens — it would
    # fit happily and report an intercept of minus infinity's numerical
    # cousin. Count the observed labels first and refuse.
    # The parse goes through as_boolean rather than .astype(bool) because a
    # CSV has no boolean type: the text "false" is a non-empty string and
    # astype(bool) calls it True, which marks every row enabled and leaves
    # this refusal unable to fire. See truthy.py.
    observed = frame[enabled_col].notna().sum()
    truthy = as_boolean(frame[enabled_col], column=enabled_col)
    if truthy.sum() == 0:
        raise TargetUnpopulatedError(
            f"{enabled_col!r} contains no True values "
            f"({observed:,} non-null of {len(frame):,} rows). The facility "
            f"panel has not arrived; run against the synthetic fixture "
            f"(models.fixtures) and label the output accordingly")

    frame[EVENT_COL] = truthy.astype("int8")
    frame = frame.sort_values([id_col, TIME_COL], kind="mergesort")

    # The first True row is the event under either encoding; see the module
    # docstring. Units that never fire get +inf so the comparison below keeps
    # all of their rows without a special case.
    event_t = (frame.loc[frame[EVENT_COL] == 1]
                    .groupby(id_col, sort=False)[TIME_COL].min())
    first_event = frame[id_col].map(event_t).fillna(np.inf)

    before = len(frame)
    frame = frame.loc[frame[TIME_COL].to_numpy() <= first_event.to_numpy()]
    dropped = before - len(frame)

    # Re-derive the event flag from the truncation rather than trusting the
    # input: under the STATE encoding every quarter after the opening is also
    # flagged True, and only the first of them is an event.
    frame[EVENT_COL] = (frame[TIME_COL].to_numpy()
                        == frame[id_col].map(event_t).to_numpy()).astype(
                            "int8")

    n_units = frame[id_col].nunique()
    n_events = int(frame[EVENT_COL].sum())
    _log.info("risk set: %d units, %d rows (%d post-event rows removed), "
              "%d events", n_units, len(frame), dropped, n_events)

    if drop_left_truncated:
        frame = _drop_left_truncated(frame, id_col)

    return frame.reset_index(drop=True)


def _drop_left_truncated(frame: pd.DataFrame, id_col: str) -> pd.DataFrame:
    """Handle units already enabled in the first observed quarter.

    A unit whose event lands on t=0 is ambiguous in a way no amount of
    modelling fixes: either it enabled in that exact quarter, or it enabled
    at some unobserved point before the window opened and we are seeing the
    tail of a spell that started earlier. Under the state encoding the two
    are literally the same rows, so nothing in the data can separate them.
    Keeping such a unit treats an unknown amount of prior exposure as zero
    exposure, which inflates the estimated hazard at t=0.

    Amazon had warehouses before 2018. Those ZCTAs are not evidence about
    what makes a ZCTA get chosen during the window; they are evidence that
    the window started late.

    Why the FIRST QUARTER goes too, and not only those units
    --------------------------------------------------------
    Dropping the units alone is a half-fix that is worse than either whole
    one, and it is the shape this function used to have. Every unit removed
    is, by construction, a unit with an event at t=0 — so what remains at
    t=0 is the set of units that did NOT have the event, and the first
    quarter contains structurally zero events. On the 1,200-unit fixture
    that turned an empirical t=0 hazard of 0.0125 into exactly 0.0000, the
    spline bent down to meet the hole, and the reported baseline came out
    ~30% low at the start of the window. The estimator was being handed a
    quarter whose outcome had been selected on.

    Selecting on the outcome at t=0 and then keeping t=0 is the error.
    Selecting on it and entering every unit at t=1 is standard DELAYED
    ENTRY: the sample is "units not yet enabled at the end of the first
    quarter", the clock keeps its calendar meaning, and every remaining
    quarter is an honest conditional probability. The price is one quarter
    of exposure out of thirty-two, and the real events that happened to land
    in it. That price is unavoidable — those events are indistinguishable
    from pre-window enablements — and paying it visibly is better than
    pretending the quarter was empty.

    ``drop_left_truncated=False`` keeps the lot, which is the right choice
    when the caller KNOWS the window opens before any unit could have
    enabled; then an event at t=0 is a real event and there is nothing to
    correct for.
    """
    t0 = int(frame[TIME_COL].min())
    truncated = frame.loc[(frame[TIME_COL] == t0) & (frame[EVENT_COL] == 1),
                          id_col].unique()
    if len(truncated) == 0:
        # No unit is flagged in the opening quarter, so there is nothing
        # ambiguous to remove and no reason to spend a quarter of exposure.
        return frame

    kept = frame.loc[~frame[id_col].isin(truncated)
                     & (frame[TIME_COL] != t0)]
    if kept.empty:
        # Returning an empty frame here would fit on nothing and report it
        # as a successful run with zero events.
        raise TargetUnpopulatedError(
            f"every unit was already enabled in the first observed quarter "
            f"(t={t0}), so the entire sample is left-truncated and there is "
            f"no risk set left. Either the window opens too late to say "
            f"anything, or the outcome column is a state flag that was "
            f"back-filled; pass drop_left_truncated=False if an event at "
            f"t={t0} really is an event")
    _log.warning(
        "left truncation at t=%d: dropping %d unit(s) already enabled in the "
        "first observed quarter, and the whole of t=%d for the remaining "
        "%d unit(s) — keeping their t=%d rows after removing every event in "
        "it would make the first quarter a structural zero",
        t0, len(truncated), t0, kept[id_col].nunique(), t0)
    return kept


def validate_risk_set(frame: pd.DataFrame, *, id_col: str = ID_COL) -> None:
    """Assert the risk-set invariants. Cheap, and it runs before every fit.

    This is the guard that makes the error in the module docstring
    impossible to commit by accident. It costs one groupby on a frame that
    is about to have a GLM run over it, which is free by comparison, and it
    turns a silently biased estimate into a loud refusal.
    """
    for col in (id_col, TIME_COL, EVENT_COL):
        if col not in frame.columns:
            raise KeyError(
                f"{col!r} missing — this frame has not been through "
                f"build_risk_set()")

    counts = frame.groupby(id_col)[EVENT_COL].sum()
    repeated = counts[counts > 1]
    if len(repeated):
        raise ValueError(
            f"{len(repeated)} unit(s) carry more than one event "
            f"(e.g. {list(repeated.index[:3])}); enablement is absorbing, so "
            f"this means the risk set was not truncated")

    # A unit that has an event must have no row after it. Comparing the
    # event time against the unit's last observed time catches exactly the
    # dense-panel mistake.
    with_event = frame.loc[frame[EVENT_COL] == 1, [id_col, TIME_COL]]
    last = frame.groupby(id_col)[TIME_COL].max()
    overrun = [
        u for u, t in with_event.itertuples(index=False) if last[u] > t]
    if overrun:
        raise ValueError(
            f"{len(overrun)} unit(s) remain in the sample after their event "
            f"(e.g. {overrun[:3]}); every one of those rows is a fabricated "
            f"non-event and will bias every coefficient toward zero")


def summarise(frame: pd.DataFrame, *, id_col: str = ID_COL) -> dict:
    """Shape of the risk set, for the metrics file and the console report."""
    return {
        "units": int(frame[id_col].nunique()),
        "rows": int(len(frame)),
        "events": int(frame[EVENT_COL].sum()),
        "event_rate": float(frame[EVENT_COL].mean()),
        "t_min": int(frame[TIME_COL].min()),
        "t_max": int(frame[TIME_COL].max()),
        "mean_quarters_at_risk": float(
            frame.groupby(id_col)[TIME_COL].size().mean()),
    }
