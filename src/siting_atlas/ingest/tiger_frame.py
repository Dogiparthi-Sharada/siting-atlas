"""The frame `tiger_lift` fits on: the panel with the highway columns on it.

Separate from the experiment because it is the only part that touches
`data/` and it is the part another module might want to reuse. The
choice of which transforms exist lives here too, so the list of
specifications being tested is one object and cannot drift between the
docstring that declares them and the code that fits them.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common import paths
from ..models.choice import ATTRACTIONS
from ..warehouse.national import load_national
from .tiger_roads import OUT as HIGHWAY

#: EXTENSIVE — counts and lengths that ADD when two ZCTAs are merged,
#: which is the property `choice.py`'s ``ln(beta'a)`` form requires and
#: the reason these are the well-specified members of the set.
EXTENSIVE = ("interchanges", "interstate_miles", "primary_road_miles")

#: INTENSIVE — decay transforms of a distance. They do not add under a
#: merger, so they break the aggregation invariance `MODEL_SPEC.md`
#: section 1 says the functional form exists to preserve. They are here
#: because `choice.py` forces ``beta > 0`` and distance-to-highway is
#: repellent: entered raw it would be driven to the boundary and read as
#: worthless whatever it is worth. Two shapes, because the shape is an
#: assumption and reporting only the better of the two would be choosing
#: the answer.
INTENSIVE = ("highway_access", "interstate_access", "interchange_decay")

COLUMNS = (*EXTENSIVE, *INTENSIVE)

#: Kilometres. The e-folding distance of the exponential alternative to
#: ``1/(1+d)``. Five kilometres is roughly a ten-minute truck trip on
#: surface streets, which is the scale at which "off the ramp and
#: straight in" stops being true.
DECAY_KM = 5.0

__all__ = ["COLUMNS", "DECAY_KM", "EXTENSIVE", "INTENSIVE",
           "highway_panel", "load_frame_inputs"]


def highway_panel() -> pd.DataFrame:
    """The panel, with the highway columns joined on and made positive.

    ``interchanges``, ``interstate_miles`` and ``primary_road_miles`` are
    counts and lengths and are legitimately zero in most ZCTAs.
    `static_frame` keeps zeros — it filters on ``>= 0`` — and ``beta'a``
    stays positive because households is the numeraire with a coefficient
    fixed at one. So nothing is floored and nothing is imputed.
    """
    if not HIGHWAY.exists():
        raise SystemExit(f"\n  {paths.rel(HIGHWAY)} not found — run "
                         "python -m siting_atlas.ingest.tiger_roads\n")
    hw = pd.read_parquet(HIGHWAY)
    hw["interchange_decay"] = np.exp(-hw["interchange_dist_km"] / DECAY_KM)
    panel = pd.read_parquet(paths.PANEL, columns=[
        "zcta", "cbsa_code", "county_geoid", "year", *ATTRACTIONS])
    return panel.merge(hw[["zcta", *COLUMNS]], on="zcta", how="left")


def load_frame_inputs():
    """Facilities, the highway-joined panel, and the lagged CBP counts."""
    expanded = (paths.ROOT / "data" / "external" / "facility_panel"
                / "national_facilities_expanded.csv")
    cbp = paths.INTERIM / "cbp_detail.parquet"
    if not cbp.exists():
        raise SystemExit(f"\n  {paths.rel(cbp)} is missing; without it the "
                         "baseline is three covariates and nothing here is "
                         "comparable to the published number.\n")
    return (load_national(expanded if expanded.exists() else None),
            highway_panel(), pd.read_parquet(cbp))
