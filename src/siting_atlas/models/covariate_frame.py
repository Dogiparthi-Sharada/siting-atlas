"""Choice sets carrying panel columns the choice model has never used.

`choice.build` reads exactly three columns out of the panel and one out of
`cbp_detail`. The panel has fifty. This module builds the same object with
any subset of those fifty attached, so an arm of `covariate_search` is a
COLUMN SUBSET of one frame rather than a separately built frame. That
matters: two frames built from different columns drop different
alternatives, and a top-k comparison between them is a comparison of
choice-set sizes wearing a covariate's name.

Three kinds of column, and the vintage rule for each
----------------------------------------------------
TIME-CONSTANT   Thirteen of the fourteen candidates. Each takes ONE value
                per ZCTA for all of 2018-2025, so there is no earlier
                value and the pre-opening vintage guard has nothing to
                bind on. That guard exists to stop a facility being
                COUNTED IN ITS OWN PREDICTOR
                (`NOTES_COVARIATE_LEAKAGE.md`), and a column that does not
                move when a building opens cannot do that. Applying the
                guard here would cost decisions and buy nothing.

                It is not a clean bill of health, and the write-up says
                so. The ACS columns are the 2023 five-year estimates
                (`data/interim/acs5_zcta_2023.parquet`, window 2019-2023)
                and EJScreen is the 2024 release, so for a 2019 decision
                the value is measured over a window that includes and
                follows the opening. That is a weaker exposure than
                self-counting and a different one, and the three BASELINE
                columns already carry it, so every arm inherits it
                equally and the comparison between arms survives.

CBP-VINTAGED    `warehousing_establishments`, exactly as `choice.build`
                does it: the latest CBP year strictly earlier than
                `open_year`, and the decision is dropped when none exists.

PANEL-VINTAGED  `permit_units_total` and `permits_yoy_pct`. 95.5% of
                ZCTAs move these year to year, so the trap
                `NOTES_COVARIATE_LEAKAGE.md` documents is live for them
                and only for them. The value used is the panel year
                strictly earlier than `open_year`, which costs every
                decision that opened in 2018 (the panel starts there).

Reciprocals, and why they exist
-------------------------------
`choice.py` enforces ``beta_k = exp(theta_k) > 0``. A column that repels
cannot be expressed; the optimiser drives it to the boundary and it reads
as useless when it is not. `median_home_value` and `diesel_pm` are both
plausibly repellent, so each is ALSO offered as ``1/x``, which is
increasing in "cheap" and "clean". This is a workaround for a
specification limit and not a free lunch: ``1/x`` is a different functional
form, not a sign flip, and like the level it is INTENSIVE, so it breaks the
aggregation invariance that `MODEL_SPEC.md` section 1 says the
``ln(beta'a)`` form exists to preserve.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common.logging_setup import get_logger
from .choice import ATTRACTIONS, ChoiceData

_log = get_logger("models.covariate_frame")

#: Panel columns with one value per ZCTA across every panel year. Measured,
#: not assumed: see `covariate_search`'s coverage block. Time-invariance is
#: NOT a defect here — the conditional logit compares alternatives inside
#: one choice set at one date and never differences a ZCTA against its own
#: past, so cross-sectional variation is the only variation it can use.
STATIC_CANDIDATES = ("traffic_proximity", "diesel_pm", "employment",
                     "annual_payroll", "median_home_value",
                     "vehicle_availability_total", "in_labor_force",
                     "bachelors_degree", "median_age", "owner_occupied",
                     "renter_occupied", "low_income_pct",
                     "people_of_colour_pct")

#: EJScreen demographic composition. Kept OUT of the headline forward
#: search and reported in an arm of its own. A model that predicts where a
#: warehouse goes from who lives there is a different object from a model
#: that predicts it from land and industry, and this project exists to
#: help communities evaluate siting decisions. That makes the inclusion a
#: choice to argue for in the open, not a column to let a greedy search
#: pick up on its own.
DEMOGRAPHIC = ("low_income_pct", "people_of_colour_pct")

#: Panel columns that move year to year and therefore need the vintage
#: rule, each as a STRICTLY POSITIVE transform of its source. ``beta'a``
#: must be positive for every alternative or the probability is undefined,
#: so a signed column cannot be entered raw.
#:
#: `permits_yoy_pct` is the panel's only forward-looking column and its
#: only flow: it measures whether construction is ACCELERATING rather than
#: whether it has happened. It is also signed. The transform used is the
#: gross growth ratio it was computed from,
#: ``1 + pct/100 = permits_t / permits_{t-1}``, which is positive
#: whenever the ratio is defined and is strictly increasing in the
#: percentage — so it is a re-expression, not a re-definition. Its
#: reciprocal is offered too, because "permits are collapsing here" is
#: as plausible a warehouse signal as "permits are booming here" and
#: `choice.py` can only express one sign at a time.
VARYING_CANDIDATES = ("permit_units_total", "permits_yoy_ratio",
                      "inv_permits_yoy_ratio")

#: The raw panel column each varying candidate is derived from.
VARYING_SOURCE = {"permit_units_total": "permit_units_total",
                  "permits_yoy_ratio": "permits_yoy_pct",
                  "inv_permits_yoy_ratio": "permits_yoy_pct"}

#: Columns offered as ``1/x`` as well as ``x``. See the module docstring.
RECIPROCALS = ("median_home_value", "diesel_pm")

#: Prefix for the reciprocal of a column, so an arm's name says what it is.
INV = "inv_"

__all__ = ["INV", "RECIPROCALS", "STATIC_CANDIDATES", "VARYING_CANDIDATES",
           "VARYING_SOURCE", "columns_only", "load_panel", "build_frame",
           "static_frame"]


def load_panel(path, static: tuple[str, ...],
               varying: tuple[str, ...]) -> pd.DataFrame:
    """The panel columns this module needs, and nothing else."""
    cols = ["zcta", "cbsa_code", "county_geoid", "year", *ATTRACTIONS,
            *static, *(VARYING_SOURCE[c] for c in varying)]
    return pd.read_parquet(path, columns=sorted(set(cols)))


def columns_only(d: ChoiceData, names: tuple[str, ...]) -> ChoiceData:
    """The same decisions and alternatives, restricted to some columns.

    The numeraire must stay first: `choice._probabilities` fixes
    ``beta[0] = 1`` by position, not by name.
    """
    if names[0] != ATTRACTIONS[0]:
        raise ValueError(f"{ATTRACTIONS[0]} must lead the column list")
    idx = [d.names.index(n) for n in names]
    return ChoiceData(d.a[:, idx], d.group, d.chosen, list(d.ids),
                      tuple(names))


def static_frame(panel: pd.DataFrame, static: tuple[str, ...],
                 reciprocals: tuple[str, ...]) -> pd.DataFrame:
    """One row per ZCTA, complete on every static column requested.

    Nothing is imputed. A ZCTA missing any requested column leaves the
    frame, and the caller reports what that cost.
    """
    keep = ["zcta", "cbsa_code", *ATTRACTIONS, *static]
    z = panel.drop_duplicates("zcta")[keep].dropna(
        subset=["cbsa_code"]).copy()
    for col in ATTRACTIONS:
        z = z[z[col].notna() & (z[col] > 0)]
    for col in static:
        z = z[z[col].notna() & (z[col] >= 0)]
    for col in reciprocals:
        z = z[z[col] > 0]
        z[INV + col] = 1.0 / z[col].to_numpy(float)
    return z


def _derive_varying(slice_: pd.DataFrame,
                    varying: tuple[str, ...]) -> pd.DataFrame:
    """The positive transforms of the signed time-varying sources.

    A year-on-year percentage of -100 means permits went to zero, so the
    growth ratio is 0 and neither it nor its reciprocal is usable. Those
    rows leave; they are not floored at some small number, because a
    floor would be an imputation and this file does not impute.
    """
    if "permits_yoy_pct" in slice_.columns:
        ratio = 1.0 + slice_["permits_yoy_pct"].to_numpy(float) / 100.0
        ratio = np.where(ratio > 0, ratio, np.nan)
        slice_ = slice_.assign(permits_yoy_ratio=ratio,
                               inv_permits_yoy_ratio=1.0 / ratio)
    return slice_[["zcta", *varying]].dropna()


def _vintage_slices(panel: pd.DataFrame, varying: tuple[str, ...]) -> dict:
    """``{panel_year: frame}`` for the time-varying columns.

    Deduplicated on (zcta, year) because the panel is quarterly and every
    one of these columns is annual — verified by `covariate_audit`, which
    reports that no ZCTA-quarter within a year differs.
    """
    raw = sorted({VARYING_SOURCE[c] for c in varying})
    out = {}
    for year, block in panel.groupby("year"):
        slice_ = block.drop_duplicates("zcta")[["zcta", *raw]].dropna(
            subset=raw)
        out[int(year)] = _derive_varying(slice_, varying)
    return out


def _pick(years: list[int], open_year: int) -> int | None:
    """Latest vintage STRICTLY earlier than the decision. The trap rule."""
    earlier = [y for y in years if y < open_year]
    return max(earlier) if earlier else None


def _blocks(static: pd.DataFrame, cbp_by_year: dict, cbp_cols: list[str],
            var_by_year: dict, var_cols: list[str],
            pair: tuple[int, int | None]) -> dict:
    """Alternatives for one (cbp vintage, panel vintage) pair, by CBSA."""
    frame = static.merge(cbp_by_year[pair[0]], on="zcta", how="left")
    # Absent from CBP for an industry means zero establishments, not an
    # unknown number. Same reasoning as `choice.build`.
    for col in cbp_cols:
        frame[col] = frame[col].fillna(0.0)
    if var_cols:
        frame = frame.merge(var_by_year[pair[1]], on="zcta", how="inner")
    return dict(iter(frame.groupby("cbsa_code")))


def build_frame(facilities: pd.DataFrame, panel: pd.DataFrame,
                cbp: pd.DataFrame, cbp_cols: tuple[str, ...],
                static: tuple[str, ...] = (),
                varying: tuple[str, ...] = (),
                reciprocals: tuple[str, ...] = ()) -> tuple[ChoiceData, dict]:
    """A ChoiceData carrying every requested column, plus a coverage report.

    Every arm of the experiment is a `columns_only` view of ONE of these,
    so all arms see identical choice sets and the paired comparison is
    about the column and nothing else.
    """
    recs = tuple(r for r in reciprocals if r in static)
    zctas_all = panel.drop_duplicates("zcta")
    z = static_frame(panel, static, recs)
    cbp_years = sorted(cbp["cbp_year"].unique().tolist())
    cbp_by_year = {y: cbp.loc[cbp["cbp_year"] == y, ["zcta", *cbp_cols]]
                   for y in cbp_years}
    var_by_year = _vintage_slices(panel, varying) if varying else {}
    var_years = sorted(var_by_year)

    names = (*ATTRACTIONS, *cbp_cols, *static,
             *(INV + c for c in recs), *varying)
    cache: dict[tuple[int, int | None], dict] = {}
    a_blocks, groups, chosen, ids = [], [], [], []
    offset = 0
    lost = {"no_panel_zcta": 0, "no_open_year": 0, "no_cbp_vintage": 0,
            "no_panel_vintage": 0, "chosen_zcta_filtered_out": 0}
    for _, fac in facilities.iterrows():
        zc = str(fac.get("zcta") or "").strip()
        try:
            open_year = int(float(fac.get("open_year")))
        except (TypeError, ValueError):
            lost["no_open_year"] += 1
            continue
        cbp_year = _pick(cbp_years, open_year)
        if cbp_year is None:
            lost["no_cbp_vintage"] += 1
            continue
        var_year = _pick(var_years, open_year) if varying else None
        if varying and var_year is None:
            lost["no_panel_vintage"] += 1
            continue
        key = (cbp_year, var_year)
        if key not in cache:
            cache[key] = _blocks(z, cbp_by_year, list(cbp_cols), var_by_year,
                                 list(varying), key)
        cbsa = z.loc[z["zcta"] == zc, "cbsa_code"]
        if not len(cbsa) or cbsa.iloc[0] not in cache[key]:
            lost["no_panel_zcta"] += 1
            continue
        alts = cache[key][cbsa.iloc[0]]
        where = np.flatnonzero(alts["zcta"].to_numpy() == zc)
        if not len(where):
            lost["chosen_zcta_filtered_out"] += 1
            continue
        a_blocks.append(alts[list(names)].to_numpy(float))
        groups.append(np.full(len(alts), len(ids)))
        chosen.append(offset + int(where[0]))
        ids.append(str(fac.get("facility_id") or len(ids)))
        offset += len(alts)

    if not a_blocks:
        raise ValueError("no usable decisions - check the zcta join")
    a = np.vstack(a_blocks)
    group = np.concatenate(groups)
    coverage = {
        "columns": list(names),
        "panel_zctas": int(len(zctas_all)),
        "frame_zctas": int(len(z)),
        "zcta_retention": float(len(z) / len(zctas_all)),
        "decisions": len(ids),
        "alternatives": int(len(a)),
        "median_choice_set": int(np.median(np.bincount(group))),
        "facilities_offered": int(len(facilities)),
        "dropped": lost,
    }
    _log.info("%d decisions, %d alternatives, %d columns",
              len(ids), len(a), len(names))
    # Same mean-scaling `choice.build` applies: it changes the units of
    # beta and nothing else, because the probability is a ratio.
    scale = a.mean(axis=0)
    return (ChoiceData(a / np.where(scale > 0, scale, 1.0), group,
                       np.array(chosen), ids, names), coverage)
