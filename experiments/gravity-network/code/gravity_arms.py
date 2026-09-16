"""The specifications `gravity_network` compares, and the one panel.

Every arm here is fitted on the SAME facility frame -- `panel_arms`'
`combined`, all 694 rows, 485 decisions -- and the same CBP vintages
carried forward to 2030 the way `panel_network.augment_cbp` carries them.
Arms differ in one thing only: which columns `choice.build` is handed.

That is the whole design. `NOTES_PANEL_EXPERIMENTS.md` §2 and §3.2 show
what happens when arms differ in their decisions as well as their
columns -- the market mix ranks the arms and the model does not. Here the
decision sets are asserted identical, so a paired difference between two
arms is attributable to the columns and to nothing else.

The baseline is the CURRENT specification, not nothing
------------------------------------------------------
`proximity_published` is `combined_plus_network`: the three columns in
`panel_network.NETWORK_COLUMNS`, which is what the project ships. It is
the number gravity has to beat. `proximity_only` drops
`network_within_50mi`, which `NOTES_PANEL_EXPERIMENTS.md` §5.1 measured
at or next to the positivity boundary at all three radii, so that the
head-to-head is two distance columns against two gravity columns rather
than three against two. `no_network` is the floor: how much of any arm's
performance is the network at all.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..common import paths
from ..common.logging_setup import get_logger
from .choice import ATTRACTIONS, CBP_ATTRACTIONS, ChoiceData, build
from .gravity_terms import (
    ALPHAS,
    MASS_MODES,
    TYPES,
    augment,
    column_name,
    gravity_columns,
    gravity_table,
    within_metro_dispersion,
)
from .panel_arms import arm_frames
from .panel_experiments import _geography
from .panel_network import NETWORK_COLUMNS, vintage_table

_log = get_logger("models.gravity_arms")

#: The facility frame every arm uses. `combined` and not `mwpvl_clean`
#: because it is the arm the published network result was measured on,
#: so the baseline in this file IS the published baseline rather than a
#: near neighbour of it.
FACILITY_ARM = "combined"

PROXIMITIES = ("sortation_proximity", "fulfilment_proximity")

BASELINE = "proximity_published"
FLOOR = "no_network"

__all__ = ["BASELINE", "FACILITY_ARM", "FLOOR", "PROXIMITIES", "GravityPanel",
           "build_arms", "build_panel", "slice_arm", "spec_columns"]


def spec_columns(alphas=ALPHAS, masses=MASS_MODES) -> dict[str, tuple]:
    """Arm name -> the ``extra`` columns `choice.build` is handed."""
    specs: dict[str, tuple] = {
        FLOOR: CBP_ATTRACTIONS,
        BASELINE: CBP_ATTRACTIONS + NETWORK_COLUMNS,
        "proximity_only": CBP_ATTRACTIONS + PROXIMITIES,
    }
    for alpha in alphas:
        for mass in masses:
            specs[f"gravity_{mass}_a{alpha:g}".replace(".", "p")] = (
                CBP_ATTRACTIONS
                + tuple(column_name(k, mass, alpha) for k in TYPES))
    return specs


@dataclass
class GravityPanel:
    """Everything needed to build an arm, plus the terms' diagnostics."""

    panel: pd.DataFrame
    frame: pd.DataFrame
    cbp: pd.DataFrame
    terms: dict

    def build(self, extra: tuple[str, ...]) -> ChoiceData:
        return build(self.frame, self.panel, self.cbp, extra)


def _inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    cbp_path = paths.INTERIM / "cbp_detail.parquet"
    if not cbp_path.exists():
        raise SystemExit(
            f"\n  {paths.rel(cbp_path)} not found\n  run: python -m "
            "siting_atlas.ingest.cbp_detail\n")
    panel = pd.read_parquet(paths.PANEL,
                            columns=["zcta", "cbsa_code", *ATTRACTIONS])
    return panel, pd.read_parquet(cbp_path)


def build_panel(alphas: tuple[float, ...] = ALPHAS) -> GravityPanel:
    """CBP joined to BOTH the published network columns and the gravity ones.

    One table, both families. `choice.build` takes only the columns an arm
    asks for, so a single augmented frame serves every arm and the
    proximity baseline is guaranteed to be reading the same vintages,
    the same centroids and the same 556 placeable facilities as the
    gravity arms. Building two frames would leave that a hope.
    """
    panel, cbp = _inputs()
    candidates, facilities, placement = _geography()
    published = vintage_table(candidates, facilities)
    gravity, diagnostics = gravity_table(candidates, facilities, alphas)
    merged = published.merge(gravity, on=["zcta", "cbp_year"], how="inner")
    if len(merged) != len(published):
        raise ValueError("the published and gravity vintage tables do not "
                         "cover the same (zcta, vintage) grid")
    columns = NETWORK_COLUMNS + gravity_columns(alphas=alphas)
    # Measured on the merged table so the published proximity columns and
    # the gravity columns are described by the SAME statistic. Without the
    # proximities in it there would be nothing to read the gravity numbers
    # against.
    dispersion = within_metro_dispersion(
        candidates, merged, columns, int(merged["cbp_year"].max()))
    frames, _ = arm_frames()
    return GravityPanel(
        panel=panel, frame=frames[FACILITY_ARM],
        cbp=augment(cbp, merged, CBP_ATTRACTIONS, columns),
        terms={"placement": placement, "dispersion": dispersion,
               **diagnostics})


def slice_arm(full: ChoiceData, extra: tuple[str, ...]) -> ChoiceData:
    """One arm as a COLUMN SLICE of the everything-at-once build.

    Exact, not an approximation, and worth stating why. `choice.build`
    divides each column by ITS OWN mean, so a column's scaled values do
    not depend on which other columns were built beside it; the rows, the
    groups, the chosen index and the decision ids do not depend on the
    columns at all. Slicing therefore produces the identical `ChoiceData`
    a separate `build` would have produced, and `build_arms` proves that
    rather than asserting it by re-building one arm the slow way and
    comparing.

    The gain is not cosmetic: a `build` walks 14 CBP vintages, merges each
    against 25,022 ZCTAs and groups by CBSA, which is ~70 seconds. Thirteen
    arms is a quarter of an hour of recomputing the same join.
    """
    names = list(ATTRACTIONS) + [c for c in extra if c not in ATTRACTIONS]
    index = [full.names.index(n) for n in names]
    return ChoiceData(full.a[:, index], full.group, full.chosen,
                      list(full.ids), tuple(names))


def build_arms(panel: GravityPanel, specs: dict[str, tuple]) -> tuple:
    """Every arm, plus the identity checks that make the pairs paired."""
    every = tuple(dict.fromkeys(c for extra in specs.values() for c in extra))
    full = panel.build(every)
    arms = {name: slice_arm(full, extra) for name, extra in specs.items()}

    # The proof that slicing == building. One arm is built the slow way
    # and compared; if this ever fails, every paired comparison in the
    # artefact is comparing two different datasets.
    rebuilt = panel.build(specs[BASELINE])
    reference = arms[FLOOR]
    ids = list(reference.ids)
    wh = reference.a[:, reference.names.index(CBP_ATTRACTIONS[0])]
    checks = {
        "n_decisions": int(reference.n_decisions),
        "n_alternatives": int(len(reference.a)),
        "decision_sets_identical": bool(
            all(list(d.ids) == ids for d in arms.values())),
        "warehousing_identical": bool(all(
            np.allclose(d.a[:, d.names.index(CBP_ATTRACTIONS[0])], wh)
            for d in arms.values())),
        "sliced_arm_equals_rebuilt_arm": bool(
            rebuilt.names == arms[BASELINE].names
            and list(rebuilt.ids) == ids
            and np.allclose(rebuilt.a, arms[BASELINE].a)),
    }
    _log.info("%d gravity arms, %d decisions, identical decision sets = %s, "
              "slice == rebuild = %s", len(arms), reference.n_decisions,
              checks["decision_sets_identical"],
              checks["sliced_arm_equals_rebuilt_arm"])
    return arms, full, checks
