"""Does the arm depend on exactly WHICH facilities could be placed?

Why this exists
---------------
`outputs/metrics/panel_experiments.json` was written at 14:41 on
2026-09-14 and `data/processed/panel.parquet` was rebuilt at 15:02 the
same day by other work in this tree. The rebuild did not touch the
choice sets or the extensive covariates -- `mwpvl_clean` still reproduces
its published top-1, top-5 and top-10 to every printed digit, and its
Brier to 1.6e-13 -- because `candidate_zctas` is 25,022 either way. What
it did touch is how many non-delivery-station facilities can be PLACED:
two more ZCTAs now carry coordinates, so 556 facilities resolve where 554
did, one extra fulfilment centre and one extra sortation centre.

That is a two-in-556 difference in the input to the two proximity
columns, and it sits between the published re-split spread and the
bootstrap in `network_inference`. It is small. "Small" is a claim, so it
is measured: refit the arm several times, each time dropping one random
sortation centre and one random fulfilment centre, and read how far the
coefficients move. That is the same KIND of perturbation as the one the
rebuild made -- two facilities in or out of the two tables that carry the
weight -- and its spread bounds it.

It does NOT identify the two facilities the rebuild added, which would
need the pre-rebuild panel, and it is not a substitute for re-running
`panel_experiments` on the current panel.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common.logging_setup import get_logger
from .choice import CBP_ATTRACTIONS, build, fit
from .network_data import EXTRA_WITH_NETWORK
from .panel_experiments import _geography
from .panel_network import (
    FULFILMENT_TABLE,
    SORTATION_TABLE,
    augment_cbp,
    vintage_table,
)

_log = get_logger("models.network_sensitivity")

#: One refit each, about a minute apiece.
SENSITIVITY_DRAWS = 5

__all__ = ["SENSITIVITY_DRAWS", "drop_two_sensitivity"]


def drop_two_sensitivity(frame: pd.DataFrame, panel: pd.DataFrame,
                         cbp: pd.DataFrame, seed: int,
                         draws: int = SENSITIVITY_DRAWS) -> dict:
    """Refit with one sortation centre and one fulfilment centre removed."""
    candidates, facilities, _ = _geography()
    tables = facilities["table"].to_numpy()
    fits: list[dict] = []
    for r in range(draws):
        rng = np.random.default_rng(seed + r)
        keep = np.ones(len(facilities), dtype=bool)
        dropped = []
        for name in (SORTATION_TABLE, FULFILMENT_TABLE):
            pick = int(rng.choice(np.flatnonzero(tables == name)))
            keep[pick] = False
            dropped.append(name)
        network = vintage_table(candidates,
                                facilities[keep].reset_index(drop=True))
        data = build(frame, panel,
                     augment_cbp(cbp, network, CBP_ATTRACTIONS),
                     EXTRA_WITH_NETWORK)
        fits.append(fit(data)["beta"])
        _log.info("facility-set sensitivity draw %d of %d: dropped %s",
                  r + 1, draws, ", ".join(dropped))

    out: dict = {
        "draws": int(draws),
        "facilities_placed": int(len(facilities)),
        "facilities_per_draw": int(len(facilities) - 2),
        "dropped_per_draw": "one random 06_us_sortation_center and one "
                            "random 01_us_fulfillment_center",
        "beta": {},
    }
    for name in fits[0]:
        values = np.array([f[name] for f in fits])
        out["beta"][name] = {
            "mean": float(values.mean()), "min": float(values.min()),
            "max": float(values.max()),
            "range": float(values.max() - values.min()),
        }
    return out
