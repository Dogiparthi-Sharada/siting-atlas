"""Alternative fits, each pre-registered as a check on the primary one.

Split out of ``diagnostics`` because these three RE-ESTIMATE the model while
everything left there only counts what is in front of it. That distinction is
worth a file boundary: a function that refits can be wrong in ways a counter
cannot, and each of these is answering "would a different, defensible choice
have given a different answer" rather than "how big is the sample".

All three are declared before the primary model is scored. A sensitivity
chosen after seeing the headline result is not a sensitivity, it is a search.
"""

from __future__ import annotations

import pandas as pd

from ..common.logging_setup import get_logger
from .base import BaselineOnly
from .diagnostics import CONTAMINATION
from .hazard import DiscreteTimeHazard, HazardSpec
from .metrics import brier_skill_score
from .risk_set import EVENT_COL, TIME_COL
from .splits import split_by_time

_log = get_logger("models.sensitivities")


def annual_sensitivity(risk: pd.DataFrame, spec: HazardSpec,
                       parts: dict) -> dict:
    """Refit at the grain the dates actually have: one row per ZCTA-year.

    Pre-registered alongside the primary fit rather than tried afterwards,
    because a sensitivity chosen after seeing the primary result is not a
    sensitivity. It collapses each unit-year to a single at-risk row, which
    removes the three structurally eventless quarters that ``event_timing``
    identifies and leaves the event count untouched.
    """
    def collapse(frame: pd.DataFrame) -> pd.DataFrame:
        agg = {c: "first" for c in frame.columns
               if c not in ("zcta", "year", EVENT_COL, TIME_COL)}
        out = frame.groupby(["zcta", "year"], as_index=False).agg(
            {EVENT_COL: "max", TIME_COL: "min", **agg})
        # One clock tick per year, so the baseline term is on the same scale
        # as the grain and the fitted hazard reads as "per year".
        out[TIME_COL] = out[TIME_COL] // 4
        return out

    annual = {k: collapse(v) for k, v in parts.items()}
    model = DiscreteTimeHazard(spec).fit(annual["train"])
    report = model.evaluate(annual["test"], label="annual-grain")
    null = BaselineOnly().fit(annual["train"]).evaluate(annual["test"])
    y = annual["test"][EVENT_COL].to_numpy()
    return {
        "ran": True,
        "rows_quarterly": int(len(risk)),
        "rows_annual": int(sum(len(v) for v in annual.values())),
        "evaluation": report.to_dict(),
        "null_model": null.to_dict(),
        "brier_skill": round(brier_skill_score(
            y, model.predict(annual["test"]).to_numpy()), 5),
    }


def temporal_check(risk: pd.DataFrame, spec: HazardSpec, *,
                   cutoff_t: int) -> dict:
    """Train on the past, score the future — and why it is SECONDARY.

    The dates are "operating by" upper bounds harvested from OSHA inspection
    records. An inspection only happens at a site that is already open, so a
    site inspected recently is dated recently whether or not it opened
    recently. That pushes mass into the late years of the panel — 2023 is
    the largest cohort — and a temporal split reads that inspection schedule
    as a build-out. The bias is in the test period specifically, which is
    the one place it cannot be argued away, so this result is reported and
    is not the headline.
    """
    parts = split_by_time(risk, cutoff_t=cutoff_t)
    if parts["train"][EVENT_COL].sum() == 0 or \
            parts["test"][EVENT_COL].sum() == 0:
        return {"ran": False,
                "reason": "one side of the temporal split has no events"}

    model = DiscreteTimeHazard(spec).fit(parts["train"])
    report = model.evaluate(parts["test"], label="temporal-holdout")
    null = BaselineOnly().fit(parts["train"]).evaluate(parts["test"])
    y = parts["test"][EVENT_COL].to_numpy()
    return {
        "ran": True,
        "cutoff_t": cutoff_t,
        "train": {"rows": len(parts["train"]),
                  "events": int(parts["train"][EVENT_COL].sum())},
        "test": {"rows": len(parts["test"]),
                 "events": int(parts["test"][EVENT_COL].sum())},
        "evaluation": report.to_dict(),
        "null_model": null.to_dict(),
        "brier_skill": round(brier_skill_score(
            y, model.predict(parts["test"]).to_numpy()), 5),
        "caveat": CONTAMINATION,
    }


def transfer_check(model: DiscreteTimeHazard,
                   heldout: pd.DataFrame) -> dict:
    """Score the metros held out of fitting. A smoke test, labelled as one.

    Phoenix and Boise were reserved to test whether the model transfers to a
    metro it has never seen. That test needs the held-out metros to contain
    enough independent openings to distinguish transfer from luck, and they
    contain one dated station each. Whatever AUC comes back describes two
    decisions. It is worth running because a catastrophic failure would
    still be informative; it is not worth quoting as geographic validation.
    """
    if heldout.empty or heldout[EVENT_COL].sum() == 0:
        return {"ran": False,
                "reason": "the held-out metros carry no observed event"}
    report = model.evaluate(heldout, label="heldout-metros")
    y = heldout[EVENT_COL].to_numpy()
    return {
        "ran": True,
        "evaluation": report.to_dict(),
        "brier_skill": round(brier_skill_score(
            y, model.predict(heldout).to_numpy()), 5),
        "n_units": int(heldout["zcta"].nunique()),
        "caveat": (
            "Phoenix and Boise hold two dated delivery stations between "
            "them, so this is a smoke test for gross failure and not a "
            "test of geographic transfer."),
    }


#: Measured, not asserted. Five addresses appear both in MWPVL's 2012 table,
#: which carries real opening months, and in the OSHA extract. The bound held
#: in 5 of 5 cases — no site was inspected before it opened — but the lag
#: from true opening to first inspection was 4, 13, 57, 69 and 345 months.
#: The 345-month case opened in 1997 and was first inspected in 2026. So the
#: bounds are VALID and can be extremely LOOSE, which is exactly the
#: combination that makes a date usable as a censoring interval and unusable
