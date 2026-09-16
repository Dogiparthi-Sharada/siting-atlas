"""Deciding which panel a run is allowed to call real.

One function, one decision, one place. The alternative — each caller doing
its own ``if path.exists()`` — is how a synthetic result eventually reaches a
slide with no label on it. Everything that could possibly want to know
whether it is looking at real data asks :func:`load_panel`, and what comes
back carries the answer with it.

The test for "real" is deliberately stricter than "the file is there". The
panel ships with ``enabled`` present and typed and entirely NULL, so a file
check passes today and tells you nothing. Real means the outcome column
contains at least one observed enablement.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..common import paths
from ..common.logging_setup import get_logger
from ..common.metros import REGISTRY
from . import truthy
from .fixtures import BANNER, SyntheticSpec, synthetic_panel

_log = get_logger("models.panel_source")

#: Prefix for every artefact built on generated data.
SYNTHETIC_PREFIX = "SYNTHETIC_"

#: Covariates used when the real panel is available.
#:
#: Three, not the five this tuple used to hold, for two independent reasons
#: and either one alone would be sufficient.
#:
#: Counting. The delivered facility panel is 49 delivery stations, 44 of which
#: open inside the window. Every ZCTA in a station's catchment flips in the
#: same quarter, so the hundreds of ZCTA-level events carry the information of
#: forty-four decisions and no more. Five covariates plus a flexible time
#: baseline is nine or ten parameters against forty-four independent events —
#: four per parameter, against a conventional floor of ten.
#:
#: Coverage. ``rent_index_yoy_pct`` is present on 30% of pilot ZCTA-quarters
#: (Zillow only publishes for dense urban ZIPs) and dropping the rows that
#: lack it takes the usable event count from 709 to 276. Paying 60% of the
#: sample for a covariate is a bad trade at any events-per-parameter ratio,
#: and the rows it costs are not missing at random — they are the less dense
#: ZCTAs, which is precisely the contrast the model is supposed to measure.
REAL_COVARIATES = (
    "households",
    "median_household_income",
    "establishments",
)


@dataclass
class PanelSource:
    """A panel plus the provenance question already answered."""

    frame: pd.DataFrame
    synthetic: bool
    covariates: tuple[str, ...]
    origin: str
    detail: dict

    def stamp(self, payload: dict) -> dict:
        """Attach the provenance to anything about to be written out."""
        return {"synthetic": self.synthetic, "panel_origin": self.origin,
                "panel_detail": self.detail, **payload}

    def filename(self, stem: str, suffix: str) -> str:
        """Prefix the artefact name when the run is synthetic."""
        prefix = SYNTHETIC_PREFIX if self.synthetic else ""
        return f"{prefix}{stem}{suffix}"


def real_panel_is_usable(path=None) -> tuple[bool, dict]:
    """Is there a panel on disk with an actually populated outcome?"""
    target = paths.PANEL if path is None else path
    if not target.exists():
        return False, {"reason": "panel.parquet not built",
                       "path": paths.rel(target)}
    try:
        outcome = pd.read_parquet(target, columns=["enabled"])["enabled"]
    except (KeyError, ValueError) as exc:
        return False, {"reason": f"no 'enabled' column ({exc})",
                       "path": paths.rel(target)}

    observed = int(outcome.notna().sum())
    # count_true, not .astype(bool): a CSV has no boolean type, and the text
    # "false" is a non-empty string that astype(bool) calls True. That would
    # report every non-null row as an enablement, declare an unpopulated
    # panel "real", and skip the SYNTHETIC_ labelling — the single worst
    # outcome available to this function. An unrecognised token raises here
    # rather than being counted as either.
    try:
        enabled = truthy.count_true(outcome, column="enabled")
    except ValueError as exc:
        return False, {"reason": f"'enabled' column is not parseable as a "
                                 f"flag ({exc})",
                       "path": paths.rel(target)}
    detail = {"path": paths.rel(target), "rows": int(len(outcome)),
              "non_null": observed, "enabled_rows": enabled}
    if enabled == 0:
        detail["reason"] = (
            "the 'enabled' column contains no True values — the facility "
            "panel has not been ingested yet")
        return False, detail
    return True, detail


def restrict_to_scope(frame: pd.DataFrame, *, heldout: bool
                      ) -> tuple[pd.DataFrame, dict]:
    """Cut the national panel down to the metros a fit is allowed to see.

    Two cuts, and skipping either one produces a result that looks fine.

    GEOGRAPHY. ``warehouse.panel`` is built over the whole 2020 gazetteer —
    33,791 ZCTAs, of which 31,585 are outside every pilot metro. Amazon has
    no delivery station within 150 miles of most of them, so their outcome is
    not "considered and not chosen", it is "never in the choice set at all".
    Left in, they make the event rate 0.08% instead of 1.8% and the model's
    discrimination becomes almost entirely the ability to tell Manhattan from
    rural Wyoming — a question nobody asked, answered with an AUC that would
    be quoted as if it were the siting result. Phoenix and Boise are declared
    held out in ``common.metros`` but nothing in the modelling path was
    honouring that declaration; ``heldout=True`` is how the transfer sample
    is fetched, deliberately by a different call than the fitting sample.

    MISSINGNESS. ``hazard.design`` refuses a NaN covariate rather than
    imputing one, so the drop has to happen somewhere explicit. Here is that
    place, and it is recorded in ``detail`` so the report can state how much
    sample the covariate list cost. ACS is pinned to one vintage and repeated
    down the quarters, so a ZCTA is missing a covariate for all of its
    quarters or for none of them; the drop removes whole units and never
    punches a hole in the middle of one unit's history.
    """
    codes = set(REGISTRY.heldout_codes if heldout else REGISTRY.fit_codes)
    before_units = int(frame["zcta"].nunique())
    scoped = frame[frame["cbsa_code"].astype("string").isin(codes)]

    present = [c for c in REAL_COVARIATES if c in scoped.columns]
    complete = scoped.dropna(subset=present) if present else scoped
    detail = {
        "scope": "heldout_metros" if heldout else "fit_metros",
        "cbsa_codes": sorted(codes),
        "units_national": before_units,
        "units_in_scope": int(scoped["zcta"].nunique()),
        "units_complete_covariates": int(complete["zcta"].nunique()),
        # Not "rows": real_panel_is_usable() already put the whole file's
        # row count under that key, and silently overwriting it would make
        # the report claim the national panel is the size of the pilot.
        "rows_in_scope": int(len(complete)),
    }
    _log.info("scope %s: %d of %d ZCTAs in the pilot metros, %d with all of "
              "%s", detail["scope"], detail["units_in_scope"], before_units,
              detail["units_complete_covariates"], list(present))
    return complete.copy(), detail


def load_panel(*, force_synthetic: bool = False,
               spec: SyntheticSpec | None = None,
               path=None, heldout: bool = False) -> PanelSource:
    """The real panel if it is usable, the labelled fixture if it is not.

    Same code path either way, which is the point: the day
    ``data/external/facility_panel/facilities.csv`` lands and the warehouse
    is rebuilt, this function starts returning real data and nothing
    downstream changes. Nobody has to remember to switch a flag, and there
    is no second, less-tested "real" branch waiting to be exercised for the
    first time on the day it matters.
    """
    usable, detail = (False, {"reason": "forced by --synthetic"}) \
        if force_synthetic else real_panel_is_usable(path)

    if usable:
        frame = pd.read_parquet(paths.PANEL if path is None else path)
        present = tuple(c for c in REAL_COVARIATES if c in frame.columns)
        missing = set(REAL_COVARIATES) - set(present)
        if missing:
            _log.warning("panel is missing covariate(s) %s; fitting without "
                         "them", sorted(missing))
        if "cbsa_code" in frame.columns:
            frame, scope = restrict_to_scope(frame, heldout=heldout)
            detail = {**detail, **scope}
        _log.info("using the REAL panel: %s", detail)
        return PanelSource(frame=frame, synthetic=False, covariates=present,
                           origin="data/processed/panel.parquet",
                           detail=detail)

    spec = spec or SyntheticSpec()
    # Repeated on every single run that touches generated data. Repetition
    # is the intent: a warning that appears once at import is a warning
    # nobody sees in a log tail.
    _log.warning("=" * 70)
    _log.warning("%s", BANNER)
    _log.warning("reason: %s", detail.get("reason", "unknown"))
    _log.warning("every artefact from this run is prefixed %s and stamped "
                 "\"synthetic\": true", SYNTHETIC_PREFIX)
    _log.warning("=" * 70)

    return PanelSource(frame=synthetic_panel(spec), synthetic=True,
                       covariates=tuple(spec.betas),
                       origin="models.fixtures.synthetic_panel",
                       detail={**detail, "spec": spec.summary()})
