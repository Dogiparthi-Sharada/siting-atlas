"""The five facility-frame compositions the experiment compares.

Why five and not one
--------------------
`NOTES_EXPANDED_REFIT.md` fitted two frames -- 104 hand-verified rows and
all 700 -- and read the difference as "more data, weaker claim". That
comparison confounds four things at once: source, OCR error, date
provenance and market mix. Splitting the frame into arms separates them.

    original_only          the 104 hand-verified rows. The reference.
    mwpvl_only             the 596 OCR'd MWPVL rows alone.
    mwpvl_clean            MWPVL rows the source vouches for AND that
                           carry a numeric opening year.
    combined               all 700.
    combined_plus_network  combined, plus the time-respecting covariates
                           in `panel_network.py`.

A sixth frame, `mwpvl_clean_plus_network`, is built by `arm_frames` and
is deliberately NOT in `ARM_NAMES`: `panel_experiments` iterates
`ARM_NAMES`, so its artefact and `NOTES_PANEL_EXPERIMENTS.md` keep
describing exactly the five arms they were written about. The sixth is
run by `network_inference.py`, which is where it is reported.

DROPPING SELECTS ON DATA AVAILABILITY, SO IT IS MEASURED
--------------------------------------------------------
`mwpvl_clean` is the only arm that drops rows, and the drop is not
random: a row with no numeric opening year is a row MWPVL printed less
about, and a row it declines to vouch for is disproportionately an
announcement rather than a building. Filtering on either could flatter
the arm by removing exactly the hard cases. `drop_profile` measures the
difference between what was dropped and what was kept on every field
that is observed for both, and the answer goes in the artefact whether
or not it is convenient.

Nothing here corrects or imputes. `PANEL_EXPANSION.md` §6 and §7.1 argue
the case for carrying a bad year rather than inventing one; this module
either keeps a row or removes it.
"""

from __future__ import annotations

import pandas as pd

from ..common import paths
from ..warehouse.national import NATIONAL_PATH, load_national
from .truthy import as_boolean

EXPANDED_PATH = (paths.ROOT / "data" / "external" / "facility_panel"
                 / "national_facilities_expanded.csv")

MWPVL_SOURCE = "mwpvl_2025q1"

ARM_NAMES = ("original_only", "mwpvl_only", "mwpvl_clean", "combined",
             "combined_plus_network")

#: Census Bureau's four regions. Used only to describe dropped rows, so a
#: row whose state is missing or unparsed is reported as "unknown"
#: instead of being assigned somewhere.
_REGION = {
    "Northeast": "CT ME MA NH RI VT NJ NY PA",
    "Midwest": "IL IN MI OH WI IA KS MN MO NE ND SD",
    "South": ("DE DC FL GA MD NC SC VA WV AL KY MS TN AR LA OK TX"),
    "West": "AZ CO ID MT NV NM UT WY AK CA HI OR WA",
}
STATE_REGION = {s: r for r, ss in _REGION.items() for s in ss.split()}

__all__ = ["ARM_NAMES", "EXPANDED_PATH", "arm_frames", "drop_profile"]


def _numeric_year(frame: pd.DataFrame) -> pd.Series:
    return pd.to_numeric(frame.get("open_year"), errors="coerce")


def arm_frames() -> tuple[dict, dict]:
    """Facility frames for the four data arms, plus how each was built.

    Both files are loaded through `warehouse.national.load_national`, so
    the declared edit ``E_operating_by`` is enforced identically on both
    and the arms differ only in which rows survive the filters here.
    """
    original = load_national(NATIONAL_PATH)
    expanded = load_national(EXPANDED_PATH)

    is_mwpvl = expanded["source_dataset"].eq(MWPVL_SOURCE)
    mwpvl = expanded[is_mwpvl]

    dated = _numeric_year(mwpvl).notna()
    vouched = as_boolean(mwpvl["mwpvl_vouched"], column="mwpvl_vouched")
    keep = dated & vouched
    clean = mwpvl[keep]

    frames = {
        "original_only": original,
        "mwpvl_only": mwpvl,
        "mwpvl_clean": clean,
        "combined": expanded,
        "combined_plus_network": expanded,
        # Not in ARM_NAMES, so `panel_experiments` still runs the five
        # arms its artefact and its notes describe. Built here because
        # `NOTES_PANEL_EXPERIMENTS.md` §7 named it as the obvious next
        # arm and `network_inference` is what runs it.
        "mwpvl_clean_plus_network": clean,
    }
    provenance = {
        "original_only": {
            "file": paths.rel(NATIONAL_PATH), "rows": int(len(original)),
            "filter": "none; E_operating_by excludes 4 of 104 at load"},
        "mwpvl_only": {
            "file": paths.rel(EXPANDED_PATH), "rows": int(len(mwpvl)),
            "filter": f"source_dataset == {MWPVL_SOURCE!r}"},
        "mwpvl_clean": {
            "file": paths.rel(EXPANDED_PATH), "rows": int(len(clean)),
            "filter": "MWPVL rows with a numeric open_year AND "
                      "mwpvl_vouched",
            "removed_no_numeric_open_year": int((~dated).sum()),
            "removed_not_vouched": int((~vouched).sum()),
            "removed_not_vouched_breakdown": {
                flag: int(as_boolean(mwpvl[flag], column=flag).sum())
                for flag in ("not_confirmed", "delayed", "cancelled")},
            "removed_either": int((~keep).sum())},
        "combined": {
            "file": paths.rel(EXPANDED_PATH), "rows": int(len(expanded)),
            "filter": "none"},
        "combined_plus_network": {
            "file": paths.rel(EXPANDED_PATH), "rows": int(len(expanded)),
            "filter": "none; adds panel_network covariates"},
        "mwpvl_clean_plus_network": {
            "file": paths.rel(EXPANDED_PATH), "rows": int(len(clean)),
            "filter": "mwpvl_clean's filter; adds panel_network "
                      "covariates"},
    }
    return frames, provenance


def _summarise(frame: pd.DataFrame) -> dict:
    """The fields a dropped row and a kept row can both be described by."""
    year = _numeric_year(frame)
    sqft = pd.to_numeric(frame.get("square_feet"), errors="coerce")
    region = frame["state"].map(STATE_REGION).fillna("unknown")
    vouched = as_boolean(frame["mwpvl_vouched"], column="mwpvl_vouched")
    return {
        "n": int(len(frame)),
        "open_year_present": int(year.notna().sum()),
        "open_year_median": (float(year.median())
                             if year.notna().any() else None),
        "square_feet_present": int(sqft.notna().sum()),
        "square_feet_median": (float(sqft.median())
                               if sqft.notna().any() else None),
        "vouched_share": float(vouched.mean()) if len(frame) else None,
        "region_share": {k: round(float(v), 4) for k, v in
                         region.value_counts(normalize=True).items()},
        "date_precision_share": {
            str(k): round(float(v), 4) for k, v in
            frame["date_precision"].fillna("missing")
            .value_counts(normalize=True).items()},
        "geo_status_share": {
            str(k): round(float(v), 4) for k, v in
            frame["geo_status"].fillna("missing")
            .value_counts(normalize=True).items()},
    }


def drop_profile() -> dict:
    """Do the rows `mwpvl_clean` removes differ from the ones it keeps?

    Reported per filter and jointly. The comparison is only possible on
    fields observed for both sides -- opening year is missing by
    construction for one of the two filters, which is itself the answer
    for that row and is why the year columns are reported as presence
    counts as well as medians.
    """
    expanded = load_national(EXPANDED_PATH)
    mwpvl = expanded[expanded["source_dataset"].eq(MWPVL_SOURCE)]
    dated = _numeric_year(mwpvl).notna()
    vouched = as_boolean(mwpvl["mwpvl_vouched"], column="mwpvl_vouched")
    keep = dated & vouched
    return {
        "kept": _summarise(mwpvl[keep]),
        "dropped_all": _summarise(mwpvl[~keep]),
        "dropped_no_numeric_open_year": _summarise(mwpvl[~dated]),
        "dropped_not_vouched": _summarise(mwpvl[~vouched]),
        "overlap_undated_and_unvouched": int((~dated & ~vouched).sum()),
    }
