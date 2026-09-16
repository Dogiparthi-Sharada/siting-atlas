"""Why the back-test failed — a horse-race that isolates the cause.

``white_space_backtest`` reports that ranking uncovered places by households
loses to ranking ALL places by households. That is a result, but on its own it
does not say WHICH part of the idea is wrong, and there are three candidates:

1. **The operationalisation.** "Is this ZCTA uncovered?" is a crude binary. A
   network planner does not ask that; they ask *how many unserved households
   would a station HERE capture*, which scores a covered ZCTA on the edge of a
   metro highly. Maybe the idea is right and the rule is blunt.
2. **A measurement artefact.** A spatially smoothed score picks contiguous
   blobs, so its top-N ZCTAs span far fewer distinct places than an unsmoothed
   one's. Comparing two such rules at a fixed N is then not a fair fight.
   :func:`concentration` measures this rather than assuming it away.
3. **The coverage conditioning itself.** Any rule that down-weights
   already-served places loses, because Amazon builds in already-served
   places.

Five rules, scored on the same held-out openings
------------------------------------------------
``households``          the baseline: households in the ZCTA, no coverage.
``white_space``         households, restricted to uncovered ZCTAs. Current.
``coverage_gain``       UNSERVED households within the radius of a station
                        placed here. The planner's version of the idea.
``load_per_facility``   households within the radius, divided by one plus the
                        facilities already within it. Densification's version:
                        build where the existing stations are over-subscribed.
``demand_in_radius``    households within the radius, **ignoring coverage
                        entirely**. The control, and the whole point of the
                        design: it shares every piece of spatial machinery
                        with ``coverage_gain`` and differs in exactly one
                        thing, the coverage mask. If ``demand_in_radius``
                        performs like ``households`` and ``coverage_gain``
                        collapses, the mask is the cause and candidates 1 and
                        2 are ruled out.

Geometry and cost
-----------------
Neighbour sums over 33,791 x 33,791 pairs are 1.1e9 haversines, which is
minutes. The same threshold test is a dot product between unit vectors —
``cos(theta) >= cos(R / R_earth)`` — so the whole thing is one matmul per
chunk and BLAS does it in seconds. Identical geometry to
``white_space_cover.nearest_miles``; only the arithmetic is rearranged.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common.logging_setup import get_logger
from ..cost.daganzo import haversine_miles
from . import white_space_backtest as bt

__all__ = ["EARTH_MILES", "N_CBSA", "N_ZCTA", "RULES", "concentration",
           "neighbour_sums", "race", "rule_scores", "unit_vectors"]

_log = get_logger("analysis.white_space")

#: Mean Earth radius, the value ``cost/daganzo.haversine_miles`` uses.
EARTH_MILES = 3958.7613

RULES = ("households", "white_space", "coverage_gain", "load_per_facility",
         "demand_in_radius")

N_ZCTA = (100, 500, 1000, 2000)
N_CBSA = (10, 25, 50, 100)

#: Rows per matmul chunk. 1,500 x 33,791 float32 is ~200MB.
CHUNK = 1500


def unit_vectors(zctas: pd.DataFrame) -> np.ndarray:
    """ZCTA centroids as unit vectors on the sphere, float32."""
    lat = np.radians(zctas["latitude"].to_numpy(float))
    lon = np.radians(zctas["longitude"].to_numpy(float))
    return np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon),
                     np.sin(lat)], axis=1).astype(np.float32)


def neighbour_sums(vectors: np.ndarray, weights: np.ndarray,
                   miles: float) -> np.ndarray:
    """For each ZCTA, the sum of ``weights`` over ZCTAs within ``miles``.

    Includes the ZCTA itself, which is correct: a station placed here serves
    the households here.
    """
    threshold = np.float32(np.cos(miles / EARTH_MILES))
    w = weights.astype(np.float32)
    out = np.zeros(len(vectors), np.float32)
    for start in range(0, len(vectors), CHUNK):
        stop = min(start + CHUNK, len(vectors))
        close = (vectors[start:stop] @ vectors.T) >= threshold
        out[start:stop] = close @ w
    return out.astype(float)


def rule_scores(zctas: pd.DataFrame, nearest: np.ndarray,
                network: pd.DataFrame, miles: float) -> dict:
    """One score array per rule in :data:`RULES`, all at the same radius."""
    vectors = unit_vectors(zctas)
    hh = zctas["households"].to_numpy(float)
    uncovered = nearest > miles
    demand = neighbour_sums(vectors, hh, miles)
    gain = neighbour_sums(vectors, np.where(uncovered, hh, 0.0), miles)

    zlat = zctas["latitude"].to_numpy(float)
    zlon = zctas["longitude"].to_numpy(float)
    n_fac = np.zeros(len(zctas))
    for lat, lon in zip(network["latitude"].to_numpy(float),
                        network["longitude"].to_numpy(float), strict=True):
        n_fac += haversine_miles(zlat, zlon, lat, lon) <= miles
    return {
        "households": hh,
        # -inf, not 0: a covered ZCTA is not merely a weak candidate under
        # this rule, it is excluded, and ranking must reflect that.
        "white_space": np.where(uncovered, hh, -np.inf),
        "coverage_gain": gain,
        "load_per_facility": demand / (1.0 + n_fac),
        "demand_in_radius": demand,
    }


def concentration(zctas: pd.DataFrame, scores: dict) -> dict:
    """Distinct CBSAs inside each rule's top-N ZCTAs.

    Candidate 2 in the module docstring, measured. A rule whose top 2,000
    ZCTAs sit in 12 metros cannot hit an opening in the 13th, however good
    its reasoning is, so a fixed-N ZCTA comparison penalises it for being
    spatially smooth rather than for being wrong.
    """
    cbsa = zctas["cbsa_code"]
    return {name: {f"top_{n}": int(cbsa.iloc[np.argsort(
        -score, kind="stable")[:n]].nunique()) for n in N_ZCTA}
        for name, score in scores.items()}


def _hit_rates(keys: pd.Series, ranked: list, cuts) -> dict:
    return {f"N_{n}": round(
        100.0 * float(keys.isin(set(ranked[:n])).mean()), 1) for n in cuts}


def _vs_baseline(keys: pd.Series, ranked: list, base: list, cuts) -> dict:
    """Paired exact McNemar for one rule against the households ranking.

    Same openings, same cut-off, so the only thing that differs is the rule.
    ``None`` where the two rules caught exactly the same openings.
    """
    out = {}
    for n in cuts:
        hit = keys.isin(set(ranked[:n])).to_numpy()
        ref = keys.isin(set(base[:n])).to_numpy()
        out[f"N_{n}"] = bt.mcnemar(hit, ref)["p_value"]
    return out


def race(zctas: pd.DataFrame, ctx: dict, coords: str, miles: float) -> dict:
    """Score every rule at one (arm, radius), at ZCTA and at metro level."""
    scores = rule_scores(zctas, ctx["nearest"], ctx["network_frame"], miles)
    openings = ctx["openings"]
    zcta_keys = openings["zcta"]
    cbsa_of = zctas.set_index("zcta")["cbsa_code"]
    cbsa_keys = zcta_keys.map(cbsa_of).dropna()
    n_metros = int(zctas["cbsa_code"].nunique())

    ranked = {}
    for name, score in scores.items():
        order = zctas["zcta"].to_numpy()[np.argsort(-score, kind="stable")]
        # A station sits at one point, so a metro is worth its best ZCTA, not
        # the sum over its ZCTAs -- summing would rank metros by how many ZIP
        # codes they happen to be cut into.
        finite = np.where(np.isfinite(score), score, 0.0)
        metros = (zctas.assign(_s=finite).dropna(subset=["cbsa_code"])
                  .groupby("cbsa_code")["_s"].max()
                  .sort_values(ascending=False).index.tolist())
        ranked[name] = (order.tolist(), metros)

    base_z, base_c = ranked["households"]
    rows = {}
    for name, (order, metros) in ranked.items():
        rows[name] = {
            "zcta_level": _hit_rates(zcta_keys, order, N_ZCTA),
            "cbsa_level": _hit_rates(cbsa_keys, metros, N_CBSA),
            "cbsa_p_vs_households": _vs_baseline(cbsa_keys, metros, base_c,
                                                 N_CBSA),
            "zcta_p_vs_households": _vs_baseline(zcta_keys, order, base_z,
                                                 N_ZCTA),
        }
    _log.info("rule race %s @ %.1f mi over %d openings", coords, miles,
              len(openings))
    return {
        "coord_set": coords,
        "radius_miles": miles,
        "openings_scored": int(len(openings)),
        "rules": rows,
        "chance_zcta": {f"N_{n}": round(100.0 * n / len(zctas), 1)
                        for n in N_ZCTA},
        "chance_cbsa": {f"N_{n}": round(100.0 * n / n_metros, 1)
                        for n in N_CBSA},
        "blob_concentration_distinct_cbsas_in_top_n":
            concentration(zctas, scores),
        "cut_year": bt.CUT_YEAR,
    }
