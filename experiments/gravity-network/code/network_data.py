"""The two network arms, built the way `panel_experiments` builds them.

Why this imports two private helpers
------------------------------------
`panel_experiments._geography` and `._network_cbp` are the construction
that produced `outputs/metrics/panel_experiments.json`. Re-implementing
them here would give a second construction that could silently drift from
the first, and then the interval this module puts on
`combined_plus_network` would be an interval on a different arm from the
one the claim is about. They are imported, deliberately, so that the
decision set is the same object and not merely the same recipe. The
assertion in `checks` is what proves it: the network arm's decision ids
must equal its no-network sibling's, and its warehousing column must be
identical to the sibling's, exactly as
`panel_experiments.decision_sets_identical_combined_vs_network` asserts
for `combined`.

The second arm
--------------
`mwpvl_clean_plus_network` is the arm `NOTES_PANEL_EXPERIMENTS.md` §7
named and nobody ran: the only filter that improved prediction crossed
with the only covariates that moved a coefficient. Its facility frame is
added to `panel_arms.arm_frames` and NOT to `panel_arms.ARM_NAMES`, so
`panel_experiments` still runs exactly the five arms its artefact and its
notes describe. Nothing already published moves because this file exists.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common import paths
from ..common.logging_setup import get_logger
from .choice import ATTRACTIONS, CBP_ATTRACTIONS, build
from .panel_arms import arm_frames
from .panel_experiments import _network_cbp
from .panel_network import NETWORK_COLUMNS

_log = get_logger("models.network_data")

#: Each network arm and the already-published arm it must reduce to when
#: the three network columns are removed.
NETWORK_ARMS: dict[str, str] = {
    "combined_plus_network": "combined",
    "mwpvl_clean_plus_network": "mwpvl_clean",
}

EXTRA_WITH_NETWORK = CBP_ATTRACTIONS + NETWORK_COLUMNS

__all__ = ["EXTRA_WITH_NETWORK", "NETWORK_ARMS", "build_network_arms"]


def _inputs():
    cbp_path = paths.INTERIM / "cbp_detail.parquet"
    if not cbp_path.exists():
        raise SystemExit(
            f"\n  {paths.rel(cbp_path)} not found\n  run: python -m "
            "siting_atlas.ingest.cbp_detail\n")
    panel = pd.read_parquet(
        paths.PANEL, columns=["zcta", "cbsa_code", *ATTRACTIONS])
    return panel, pd.read_parquet(cbp_path)


def build_network_arms() -> dict:
    """One `ChoiceData` per network arm, plus the sibling it extends.

    Returns a dict keyed by arm name. Each entry holds the arm's data,
    the no-network sibling's data, and the two identity checks that make
    the pair a PAIRED comparison rather than two unrelated fits.
    """
    panel, cbp = _inputs()
    net_cbp, diagnostics = _network_cbp(cbp)
    frames, provenance = arm_frames()

    out: dict = {"network_facilities": diagnostics, "arms": {},
                 "panel": panel, "cbp": cbp, "frames": frames}
    for arm, base in NETWORK_ARMS.items():
        with_net = build(frames[arm], panel, net_cbp, EXTRA_WITH_NETWORK)
        without = build(frames[base], panel, cbp, CBP_ATTRACTIONS)
        wh = with_net.names.index(CBP_ATTRACTIONS[0])
        same_ids = list(with_net.ids) == list(without.ids)
        out["arms"][arm] = {
            "data": with_net,
            "baseline": without,
            "baseline_arm": base,
            "provenance": provenance[arm],
            "checks": {
                "n_decisions": int(with_net.n_decisions),
                "n_decisions_baseline": int(without.n_decisions),
                "n_alternatives": int(len(with_net.a)),
                "decision_sets_identical": bool(same_ids),
                "warehousing_identical": bool(
                    same_ids and np.allclose(
                        with_net.a[:, wh],
                        without.a[:, without.names.index(
                            CBP_ATTRACTIONS[0])])),
            },
        }
        _log.info("%s: %d decisions, %d alternatives, identical to %s = %s",
                  arm, with_net.n_decisions, len(with_net.a), base, same_ids)
    return out


def size_buckets(d) -> np.ndarray:
    """Choice-set size per decision, for the stratified reporting."""
    return np.bincount(d.group)
