"""The secondary re-splits, and the interval that is allowed to be quoted.

Prereg section 6 asks for both and is explicit that they are different
things:

> A percentile spread across re-splits is not a standard error. Measured
> here: a metro-clustered bootstrap came out 24-28% WIDER than the re-split
> spread on more data (`outputs/metrics/network_inference.json`).

So the re-split block reports a SPREAD and says so in its own key names, and
the uncertainty a reader may quote comes from `clustered_bootstrap`, which
resamples metros with replacement. Metros, not metro-years: the same metro
appears eight times in the frame and its eight rows are not eight
independent draws.

The re-splits hold out whole METROS for the same reason. A random split of
metro-years would put Chicago 2019 in training and Chicago 2020 in test,
and the covariates are near-constant within a metro, so the model would be
scored partly on rows it had already seen.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common.seeds import seed
from .metro_eval import baseline_scores, score_predictions
from .metro_fit import fit_arm

__all__ = ["paired_resplits", "clustered_bootstrap"]


def paired_resplits(frame: pd.DataFrame, columns: list[str], *,
                    form: str = "logit", n_repeats: int = 50,
                    holdout: float = 0.3) -> dict:
    """Refit inside every repeat; hold out 30% of metros each time.

    Paired: the model and all three baselines are scored on exactly the same
    held-out rows in every repeat, so the per-repeat difference is a
    difference on the same units. Prereg section 8.3 rules out reading an
    unpaired gap as a result, and this is where that rule bites.
    """
    rng = np.random.default_rng(seed("evaluation", "train_test_split"))
    metros = frame["cbsa_code"].drop_duplicates().to_numpy()
    n_hold = max(1, int(round(holdout * len(metros))))
    y = frame["any_event"].to_numpy(float)
    rows = []
    for _ in range(n_repeats):
        held = set(rng.choice(metros, size=n_hold, replace=False))
        test = frame["cbsa_code"].isin(held).to_numpy()
        train = ~test
        pred = fit_arm(frame, columns, train=train, test=test, form=form)
        base = baseline_scores(frame, test, pred.null_p)
        rec = {"model": score_predictions(y[test], pred.p[test])}
        for name, (s, p) in base.items():
            rec[name] = score_predictions(y[test], p, s)
        rows.append(rec)

    out = {"n_repeats": n_repeats, "holdout_metros": n_hold,
           "seed": seed("evaluation", "train_test_split"),
           "note": ("spread across re-splits, NOT a standard error "
                    "(prereg section 6)")}
    for arm in rows[0]:
        for metric in ("auc", "brier", "ece", "top50"):
            vals = np.array([r[arm][metric] for r in rows
                             if r[arm][metric] is not None], dtype=float)
            if not len(vals):
                continue
            out.setdefault(arm, {})[metric] = {
                "mean": round(float(vals.mean()), 6),
                "spread_p2.5": round(float(np.percentile(vals, 2.5)), 6),
                "spread_p97.5": round(float(np.percentile(vals, 97.5)), 6),
            }
    diffs = np.array([r["model"]["auc"] - r["baseline2_households"]["auc"]
                      for r in rows
                      if r["model"]["auc"] is not None
                      and r["baseline2_households"]["auc"] is not None])
    out["paired_auc_model_minus_baseline2"] = {
        "mean": round(float(diffs.mean()), 6),
        "wins": int((diffs > 0).sum()), "losses": int((diffs < 0).sum()),
        "ties": int((diffs == 0).sum()),
        "spread_p2.5": round(float(np.percentile(diffs, 2.5)), 6),
        "spread_p97.5": round(float(np.percentile(diffs, 97.5)), 6),
    }
    return out


def clustered_bootstrap(metro: np.ndarray, y: np.ndarray,
                        arms: dict[str, np.ndarray], *,
                        reference: str, n_boot: int = 2000) -> dict:
    """Metro-clustered percentile interval on AUC and on AUC differences.

    Operates on predictions already made out of time, so it measures the
    sampling variability of the metrics given the fitted models -- not the
    variability of refitting. That is the right object for "is this AUC gap
    distinguishable from zero on 935 metros", and it is the wider of the two
    intervals the prereg contrasts.
    """
    from .metrics import roc_auc

    rng = np.random.default_rng(seed("uncertainty", "bootstrap"))
    uniq = np.unique(metro)
    index = {m: np.flatnonzero(metro == m) for m in uniq}
    names = list(arms)
    draws = {n: [] for n in names}
    diffs = {n: [] for n in names if n != reference}
    for _ in range(n_boot):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([index[m] for m in pick])
        yb = y[idx]
        if yb.sum() == 0 or yb.sum() == len(yb):
            continue
        got = {}
        for n in names:
            a = roc_auc(yb, arms[n][idx])
            got[n] = a
            if np.isfinite(a):
                draws[n].append(a)
        for n in diffs:
            if np.isfinite(got[n]) and np.isfinite(got[reference]):
                diffs[n].append(got[n] - got[reference])

    def _pct(v):
        v = np.asarray(v, dtype=float)
        if not len(v):
            return None
        return {"mean": round(float(v.mean()), 6),
                "ci2.5": round(float(np.percentile(v, 2.5)), 6),
                "ci97.5": round(float(np.percentile(v, 97.5)), 6),
                "n_draws": int(len(v))}

    return {"n_boot": n_boot, "cluster": "cbsa_code",
            "n_clusters": int(len(uniq)),
            "seed": seed("uncertainty", "bootstrap"),
            "auc": {n: _pct(v) for n, v in draws.items()},
            f"auc_minus_{reference}": {n: _pct(v) for n, v in diffs.items()}}
