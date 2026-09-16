"""Baselines, per-year scoring, and the size strata prereg section 6 asks for.

The three baselines are fixed by prereg section 5 and the second is the bar:

    1  uniform across metros                 the no-information floor
    2  rank by households                    THE ONE THAT MATTERS
    3  rank by facilities already present    the densification null

"Rank by households" is a ranking, which is all AUC and top-k need. Brier and
ECE need a probability, so the ranking is turned into one by allocating the
training base rate across metros in proportion to the score, capped at 1 with
the excess redistributed. That construction has no fitted parameter, keeps the
ranking exactly, and puts the mean predicted probability on the training base
rate -- so the baseline is not handicapped on calibration by an arbitrary
scale choice.

Reporting follows section 6: raw Brier and top-k against a uniform null, never
a skill score, because skill scores are improper (Gneiting & Raftery 2007
sec. 2.3, p.362).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .metrics import brier_score, expected_calibration_error, roc_auc
from .metro_fit import fit_arm

__all__ = ["TOP_K", "allocate", "baseline_scores", "score_predictions",
           "size_tiers", "out_of_time"]

#: 935 metros, 21-64 of which receive an opening in a given year. k=25 is
#: about the smallest year's event count and k=50 about the largest.
TOP_K = (25, 50)


def allocate(score: np.ndarray, total: float) -> np.ndarray:
    """Spread `total` expected events over metros in proportion to `score`.

    Capped at 1 per metro with the remainder redistributed, so the result is
    a probability vector whose sum is `total` whenever that is feasible. A
    plain proportional rule would hand New York a "probability" of 2.8.
    """
    s = np.asarray(score, dtype=float).copy()
    s = np.where(np.isfinite(s) & (s > 0), s, 0.0)
    p = np.zeros_like(s)
    free = np.ones_like(s, dtype=bool)
    remaining = float(total)
    for _ in range(50):
        pool = s[free].sum()
        if pool <= 0 or remaining <= 1e-12:
            break
        add = remaining * s / pool
        newp = np.where(free, np.minimum(1.0, p + add), p)
        spent = float((newp - p).sum())
        capped = free & (newp >= 1.0 - 1e-12)
        p = newp
        remaining -= spent
        if not capped.any():
            break
        free = free & ~capped
    return np.clip(p, 1e-9, 1 - 1e-9)


def baseline_scores(frame: pd.DataFrame, test: np.ndarray,
                    null_p: float) -> dict:
    """The three prereg baselines on the held-out rows.

    Returned as (score, p) pairs: `score` drives AUC and top-k, `p` drives
    Brier and ECE.
    """
    n = int(test.sum())
    total = null_p * n
    hh = frame.loc[test, "households"].to_numpy(float)
    fac = frame.loc[test, "facilities_open_prior"].to_numpy(float)
    out = {
        "baseline1_uniform": (np.zeros(n), np.full(n, null_p)),
        "baseline2_households": (hh, allocate(hh, total)),
        "baseline3_facilities": (fac, allocate(fac, total)),
    }
    return out


def _topk(y: np.ndarray, score: np.ndarray, k: int) -> tuple[int, int]:
    """Events captured by the k highest scores, and how many ties at the cut.

    Ranking is on the score alone with `np.argsort(kind="stable")`, so the
    frame's own row order breaks ties. Baseline 3 is mostly zeros -- 740 of
    935 metros have never had a facility -- and its top-k is therefore
    partly an artefact of that order. The tie count says how much.
    """
    k = min(k, len(score))
    order = np.argsort(-score, kind="stable")[:k]
    cut = score[order[-1]] if k else np.inf
    ties = int((score == cut).sum())
    return int(y[order].sum()), ties


def score_predictions(y: np.ndarray, p: np.ndarray,
                      score: np.ndarray | None = None) -> dict:
    """AUC, Brier, ECE and top-k for one arm on one held-out set."""
    s = p if score is None else score
    row = {
        "n": int(len(y)),
        "n_events": int(y.sum()),
        "auc": _r(roc_auc(y, s)),
        "brier": _r(brier_score(y, p), 8),
        "ece": _r(expected_calibration_error(y, p), 6),
        "mean_p": _r(float(np.mean(p)), 6),
    }
    for k in TOP_K:
        hits, ties = _topk(y, s, k)
        row[f"top{k}"] = hits
        row[f"top{k}_ties_at_cut"] = ties
        row[f"top{k}_uniform_null"] = _r(k * float(y.sum()) / len(y), 3)
    return row


def _r(v, nd: int = 4):
    return None if v is None or not np.isfinite(v) else round(float(v), nd)


def size_tiers(frame: pd.DataFrame, n_tiers: int = 3) -> pd.Series:
    """Metro size tier, from 2023 households, fixed across all years.

    Fixed rather than recomputed per year so that "tier 3" names the same
    metros in every row and a per-tier AUC is a statement about one set of
    places. The vintage of the cut is 2023, which is fine for a REPORTING
    stratification -- it never enters a prediction -- and is stated because
    the same column is inadmissible as a covariate for exactly that reason.
    """
    by_metro = (frame.drop_duplicates("cbsa_code")
                .set_index("cbsa_code")["households"])
    labels = [f"tier{i + 1}" for i in range(n_tiers)]
    cut = pd.qcut(by_metro.rank(method="first"), n_tiers, labels=labels)
    return frame["cbsa_code"].map(cut).astype(object)


def out_of_time(frame: pd.DataFrame, columns: list[str], form: str,
                held_out) -> tuple[dict, dict]:
    """Prereg section 6, primary: fit through t-1, predict t, roll forward.

    Returns the per-year table and the pooled held-out vectors, the latter
    so that a metro-clustered bootstrap and the size strata can be computed
    on exactly the predictions that were scored, rather than on a refit.
    """
    y = frame["any_event"].to_numpy(float)
    yr = frame["year"].to_numpy()
    keys = ("p", "hh", "hh_p", "fac", "fac_p", "y", "metro", "null")
    per_year, pooled = {}, {k: [] for k in keys}
    for t in held_out:
        train, test = yr < t, yr == t
        pred = fit_arm(frame, columns, train=train, test=test, form=form)
        base = baseline_scores(frame, test, pred.null_p)
        blk = {"model": score_predictions(y[test], pred.p[test]),
               "constant_null": score_predictions(
                   y[test], np.full(int(test.sum()), pred.null_p)),
               "fit": pred.diagnostics}
        for name, (s, p) in base.items():
            blk[name] = score_predictions(y[test], p, s)
        per_year[t] = blk
        pooled["p"].append(pred.p[test])
        pooled["null"].append(np.full(int(test.sum()), pred.null_p))
        pooled["hh"].append(base["baseline2_households"][0])
        pooled["hh_p"].append(base["baseline2_households"][1])
        pooled["fac"].append(base["baseline3_facilities"][0])
        pooled["fac_p"].append(base["baseline3_facilities"][1])
        pooled["y"].append(y[test])
        pooled["metro"].append(frame.loc[test, "cbsa_code"].to_numpy())
    return per_year, {k: np.concatenate(v) for k, v in pooled.items()}
