"""Gravity terms over the already-open Amazon non-delivery-station network.

What this is, and why it is the next test
-----------------------------------------
`COVARIATES_TRIED.md` §1.3 records the one covariate class that has ever
landed in the interior, and the one line in it that is easy to read past:

    sortation_proximity    0.118 [0.018, 0.235]   interior
    fulfilment_proximity   0.178 [0.028, 0.334]   interior
    network_within_50mi    AT THE BOUNDARY at 25, 50 AND 100 miles

A CONTINUOUS DISTANCE to the single nearest facility works. A COUNT of
facilities inside a radius fails at every radius tried. Both discard
information, and they discard DIFFERENT information: the distance throws
away every facility but one, the count throws away every distance.

A gravity term keeps both. For candidate ZCTA ``i``,

    G_i(alpha) = sum_j  mass_j / (1 + d_ij) ** alpha

summed over the facilities ``j`` of one type that were ALREADY OPEN when
the decision was made.

The kernel is the SAME kernel, deliberately
-------------------------------------------
`panel_network._proximity` is ``1 / (1 + miles)`` to the nearest facility.
This module's alpha=1 count-mass term is ``sum_j 1 / (1 + miles_ij)`` over
the whole network of that type. So the baseline takes the MAX of a set of
terms and this takes the SUM of the IDENTICAL terms. Nothing else differs,
which is what makes the comparison in `gravity_network.py` a clean test of
"max versus sum" rather than a test of two unrelated kernels.

``1 + d`` rather than ``d``: a candidate ZCTA can BE the facility's ZCTA,
where ``1/d**alpha`` diverges. The shift also keeps the term bounded by the
facility count, so a vintage with no facilities scores 0, which is the
limit of the kernel and the value `panel_network` already uses.

TIME-RESPECTING, BY THE SAME MECHANISM AND NOT A NEW ONE
--------------------------------------------------------
The vintage machinery is `panel_network`'s: 14 annual vintages, vintage
``Y`` holding only ``open_year <= Y``, and a decision scored on the latest
vintage strictly earlier than its own opening year. A facility that cannot
be dated is excluded by `panel_network.load_network_facilities` before it
reaches this module, so it can never enter a sum. `NOTES_COVARIATE_LEAKAGE`
is the reason this is structural rather than a filter.

THE HONEST COST, WHICH IS THE SAME COST AND SLIGHTLY WORSE
-----------------------------------------------------------
A gravity term is not EXTENSIVE. Merging two ZCTAs does not add their
attractions, so `MODEL_SPEC.md` §1's zone-merger invariance -- bought from
Train §3.4 Example 2 and the whole justification for the ``ln(beta'a)``
form -- does not hold. The existing proximities already pay this and say
so. Gravity pays one thing more: its LEVEL grows as the network grows, and
in a share model ``P_j = beta'a_j / sum_k beta'a_k`` a common additive
shift across a choice set does NOT cancel, it flattens the distribution
towards uniform. `gravity_network` reports the per-vintage mean so a reader
can see how big that drift is.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common.logging_setup import get_logger
from .panel_network import (
    FULFILMENT_TABLE,
    SORTATION_TABLE,
    VINTAGE_FIRST,
    VINTAGE_LAST,
    _distance_matrix,
)

_log = get_logger("models.gravity_terms")

#: Distance exponents. 1 and 2 are the brief's; 3 is added because the
#: sum converges on its largest term as alpha grows, so alpha=3 is the
#: end of the family where gravity degenerates towards "the nearest
#: facility and nothing else" -- the baseline. Running 1, 2, 3 therefore
#: reads as a path from "the whole network counts equally-ish" to "only
#: the nearest one counts", and the shape of that path is the answer.
#:
#: alpha=0 is NOT run and the reason is that it is degenerate, not that
#: it is uninteresting: ``(1+d)**0 == 1`` makes G_i the total number of
#: open facilities, identical for every ZCTA in the country at a given
#: vintage, so it carries exactly zero within-choice-set variation.
ALPHAS: tuple[float, ...] = (1.0, 2.0, 3.0)

#: ``count``             every placeable facility, mass 1.
#: ``sqft``              square feet, for the facilities MWPVL states it
#:                       for; the rest contribute 0, i.e. they leave the
#:                       sum entirely.
#: ``count_sqft_subset`` mass 1 on EXACTLY the facilities ``sqft`` uses.
#:
#: The third is the control, and without it the count/sqft comparison is
#: uninterpretable: ``sqft`` differs from ``count`` in two ways at once
#: (it weights by size AND it drops the facilities with no stated size),
#: so a difference between them could be either. ``count_sqft_subset``
#: holds the network fixed and varies only the weighting.
MASS_MODES: tuple[str, ...] = ("count", "sqft", "count_sqft_subset")

#: The two facility types the existing covariates are split on, kept
#: separate for the same reason: an FC feeds a sortation centre feeds a
#: delivery station, so the two legs are different flows and there is no
#: reason their coefficients should be equal.
TYPES: dict[str, str] = {"sortation": SORTATION_TABLE,
                         "fulfilment": FULFILMENT_TABLE}

#: Cosmetic. `choice.build` divides every column by its own mean, so the
#: fit is invariant to this; it only keeps the raw numbers in the
#: artefact readable as "millions of square feet".
SQFT_SCALE = 1e6

__all__ = ["ALPHAS", "LARGE_METRO_MIN", "MASS_MODES", "SQFT_SCALE", "TYPES",
           "augment", "column_name", "facility_mass", "gravity_columns",
           "gravity_table", "within_metro_dispersion"]


def column_name(kind: str, mass: str, alpha: float) -> str:
    """``sortation_gravity_sqft_a2``-style name for one term."""
    return f"{kind}_gravity_{mass}_a{alpha:g}".replace(".", "p")


def gravity_columns(kinds=tuple(TYPES), masses=MASS_MODES,
                    alphas=ALPHAS) -> tuple[str, ...]:
    """Every column `gravity_table` will emit, in a stable order."""
    return tuple(column_name(k, m, a)
                 for a in alphas for k in kinds for m in masses)


def facility_mass(facilities: pd.DataFrame) -> tuple[dict, dict]:
    """The three mass vectors, and how much square footage is stated.

    A facility with no stated square footage gets mass 0 under ``sqft``,
    which removes it from the sum rather than imputing a size for it.
    `panel_arms` and `PANEL_EXPANSION.md` §6 take the same line: carry a
    gap as a gap, never invent a value. The cost is that the ``sqft``
    network is a subset of the ``count`` network, which is exactly what
    ``count_sqft_subset`` exists to hold fixed.
    """
    sqft = pd.to_numeric(facilities["sqft"], errors="coerce").to_numpy(float)
    known = np.isfinite(sqft) & (sqft > 0)
    masses = {
        "count": np.ones(len(facilities)),
        "sqft": np.where(known, sqft, 0.0) / SQFT_SCALE,
        "count_sqft_subset": known.astype(float),
    }
    table = facilities["table"].to_numpy()
    coverage = {
        "placeable_facilities": int(len(facilities)),
        "square_feet_stated": int(known.sum()),
        "square_feet_stated_share": float(known.mean()),
        "sqft_scale_divisor": SQFT_SCALE,
        "by_type": {
            kind: {
                "placeable": int((table == name).sum()),
                "square_feet_stated": int((known & (table == name)).sum()),
                "median_square_feet": (
                    float(np.median(sqft[known & (table == name)]))
                    if (known & (table == name)).any() else None),
            } for kind, name in TYPES.items()},
    }
    _log.info("gravity mass: %d of %d placeable facilities state square "
              "footage (%.1f%%)", coverage["square_feet_stated"],
              len(facilities), 100 * coverage["square_feet_stated_share"])
    return masses, coverage


def gravity_table(candidates: pd.DataFrame, facilities: pd.DataFrame,
                  alphas: tuple[float, ...] = ALPHAS) -> tuple:
    """One row per (ZCTA, vintage year); gravity as the network then stood.

    Vintage ``Y`` sums only over facilities with ``open_year <= Y``, so a
    decision taken in ``Y+1`` sees a network every member of which opened
    strictly before it. This is `panel_network.vintage_table`'s rule and
    the distance matrix is `panel_network`'s function, imported rather
    than re-derived so the two tables cannot drift apart on geometry.
    """
    d = _distance_matrix(candidates, facilities)
    masses, coverage = facility_mass(facilities)
    years = facilities["open_year"].to_numpy(float)
    table = facilities["table"].to_numpy()
    zcta = candidates["zcta"].to_numpy()
    mass_names = list(masses)
    stack = np.stack([masses[m] for m in mass_names], axis=1)

    per_vintage: dict[int, dict] = {
        v: {} for v in range(VINTAGE_FIRST, VINTAGE_LAST + 1)}
    for alpha in alphas:
        # float32 throughout: the inputs are ZCTA-centroid distances with
        # a 1.30 circuity factor bolted on, so the seventh significant
        # figure was never meaningful, and the full matrix is 25k x 556.
        w = np.power(1.0 / (1.0 + d), np.float32(alpha))
        for kind, name in TYPES.items():
            is_kind = table == name
            for vintage in per_vintage:
                sel = (is_kind & (years <= vintage)).astype(np.float32)
                vals = w @ (stack * sel[:, None]).astype(np.float32)
                for j, mass in enumerate(mass_names):
                    per_vintage[vintage][column_name(kind, mass, alpha)] = (
                        vals[:, j].astype(float))

    frames = [pd.DataFrame({"zcta": zcta, "cbp_year": v, **cols})
              for v, cols in per_vintage.items()]
    out = pd.concat(frames, ignore_index=True)
    drift = {
        col: {str(v): float(out.loc[out["cbp_year"] == v, col].mean())
              for v in (VINTAGE_FIRST, 2020, VINTAGE_LAST)}
        for col in gravity_columns(alphas=alphas)}
    return out, {**coverage, "mean_by_vintage": drift,
                 "vintages": int(out["cbp_year"].nunique()),
                 "candidate_zctas": int(len(candidates))}


#: A choice set this size or larger is `panel_strata`'s LARGE stratum,
#: where lift is not structurally capped and a siting decision is
#: genuinely contested. Dispersion is measured there because that is the
#: stratum the covariate has to work in.
LARGE_METRO_MIN = 101


def within_metro_dispersion(candidates: pd.DataFrame, table: pd.DataFrame,
                            columns: tuple[str, ...], vintage: int) -> dict:
    """Mean within-CBSA coefficient of variation, large metros only.

    A conditional choice model compares alternatives INSIDE a choice set,
    so between-metro variation is differenced away by construction and a
    column's only currency is how much it varies among the candidate
    ZCTAs of one metro. `COVARIATES_TRIED.md` §1.1 diagnoses six of
    eighteen failed columns this way: county figures broadcast to every
    ZCTA offer nine distinct values per two hundred candidates and a
    near-constant cannot rank anything.

    A gravity term can fail the same way for a different reason. As alpha
    falls, the sum spreads over the whole national network and becomes a
    smooth continental gradient -- large, but nearly the same for every
    ZCTA of one metro. This function measures that directly instead of
    asserting it: sd/mean within each large CBSA, averaged over CBSAs, at
    the last vintage. It is a dispersion, not a distinct-value count,
    because a gravity term is continuous and every value is distinct.
    """
    home = candidates.set_index("zcta")["cbsa_code"]
    slab = table.loc[table["cbp_year"] == vintage].copy()
    slab["cbsa_code"] = slab["zcta"].map(home)
    slab = slab.dropna(subset=["cbsa_code"])
    sizes = slab["cbsa_code"].value_counts()
    large = slab[slab["cbsa_code"].isin(sizes[sizes >= LARGE_METRO_MIN].index)]
    grouped = large.groupby("cbsa_code")[list(columns)]
    cv = grouped.std(ddof=0) / grouped.mean().replace(0.0, np.nan)
    return {"vintage": int(vintage),
            "large_metro_min_candidates": LARGE_METRO_MIN,
            "large_metros": int(large["cbsa_code"].nunique()),
            "candidate_zctas_in_large_metros": int(len(large)),
            "mean_within_metro_cv": {c: (float(cv[c].mean())
                                         if cv[c].notna().any() else None)
                                     for c in columns}}


def augment(cbp: pd.DataFrame, table: pd.DataFrame, extra: tuple[str, ...],
            columns: tuple[str, ...]) -> pd.DataFrame:
    """`panel_network.augment_cbp`, generalised over which columns join.

    A near-copy, and the duplication is deliberate: `panel_network` is
    owned by another workstream and its `augment_cbp` hard-codes
    `NETWORK_COLUMNS`. Editing it to take a column list would change the
    module that produced `panel_experiments.json`. The join rule, the
    vintage range and the carry-forward of the last CBP slab are
    identical, and `gravity_arms` asserts that the published proximity
    columns coming out of this function reproduce the published arm's
    decision set exactly.
    """
    last = int(cbp["cbp_year"].max())
    parts = []
    for vintage in range(VINTAGE_FIRST, VINTAGE_LAST + 1):
        slab = cbp.loc[cbp["cbp_year"] == min(vintage, last),
                       ["zcta", *extra]].copy()
        net = table.loc[table["cbp_year"] == vintage, ["zcta", *columns]]
        merged = slab.merge(net, on="zcta", how="outer")
        merged["cbp_year"] = vintage
        parts.append(merged)
    return pd.concat(parts, ignore_index=True)
