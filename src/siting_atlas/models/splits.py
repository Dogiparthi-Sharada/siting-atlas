"""Train / calibration / test splits that respect the panel's grain.

The trap
--------
A risk set has up to 32 rows for the same ZCTA. Split those rows at random
and 2024Q1 for ZCTA 94608 lands in training while 2024Q2 for the same ZCTA
lands in test. The covariates are nearly identical — it is the same place a
quarter later — so the model has effectively seen the answer. Held-out AUC
comes back at 0.95, everyone is delighted, and the number means nothing.

Splitting by UNIT instead of by row keeps every quarter of a ZCTA on one
side of the wall. The held-out AUC then answers the question that was
actually asked: given a ZCTA the model has never seen, can it rank it.

A second, harder question — can it predict a FUTURE quarter — needs a
temporal split, which is :func:`split_by_time` below. Both are offered
because they answer different questions and a backtest wants the temporal
one.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common.logging_setup import get_logger
from ..common.seeds import seed
from .risk_set import ID_COL, TIME_COL

_log = get_logger("models.splits")

Split = dict[str, pd.DataFrame]


def split_by_unit(frame: pd.DataFrame, *, fractions=(0.6, 0.2, 0.2),
                  id_col: str = ID_COL,
                  seed_name: str = "train_test_split") -> Split:
    """Partition whole units into train / calibration / test.

    Three ways, not two: split conformal needs a calibration sample that the
    model never saw, and reusing the training rows for it destroys the
    coverage guarantee — the residuals on training data are optimistically
    small, so the conformal quantile comes out too tight and coverage falls
    below nominal. The guarantee is the whole point of conformal, so the
    third split is not optional.
    """
    if not np.isclose(sum(fractions), 1.0):
        raise ValueError(f"fractions must sum to 1, got {sum(fractions)}")

    units = np.sort(frame[id_col].unique())
    rng = np.random.default_rng(seed("evaluation", seed_name))
    rng.shuffle(units)

    n = len(units)
    cut1 = int(round(fractions[0] * n))
    cut2 = cut1 + int(round(fractions[1] * n))
    groups = {"train": units[:cut1], "calibration": units[cut1:cut2],
              "test": units[cut2:]}

    out = {k: frame[frame[id_col].isin(set(v))].copy()
           for k, v in groups.items()}
    _log.info("split by unit: %s", ", ".join(
        f"{k} {len(v):,} rows / {len(groups[k]):,} units"
        for k, v in out.items()))
    _warn_if_eventless(out)
    return out


def split_by_time(frame: pd.DataFrame, *, cutoff_t: int,
                  time_col: str = TIME_COL) -> Split:
    """Everything up to ``cutoff_t`` trains; everything after is held out.

    This is the honest backtest and it will score worse than the unit split,
    because it also has to extrapolate the time baseline past the last
    quarter it saw. Worse, and more like the real task.
    """
    train = frame[frame[time_col] <= cutoff_t].copy()
    test = frame[frame[time_col] > cutoff_t].copy()
    _log.info("split by time at t=%d: train %d rows, test %d rows",
              cutoff_t, len(train), len(test))
    return {"train": train, "test": test}


def _warn_if_eventless(split: Split, event_col: str = "event") -> None:
    """A split with no events silently makes AUC undefined downstream."""
    for name, part in split.items():
        if event_col in part.columns and part[event_col].sum() == 0:
            _log.warning(
                "the %s split contains no events — AUC is undefined there "
                "and the conformal quantile will be one-sided; increase the "
                "sample or the event rate", name)
