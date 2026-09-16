"""L5 — figures rendered FROM cost-model output.

One import surface for the four charts, so the batch builder
(``siting_atlas.viz.build``) and the dashboard
(``siting_atlas.app.dashboard``) cannot drift into drawing different
pictures from the same parquet.

    from siting_atlas.viz import load, cost_vs_density
    fig = cost_vs_density(load(2023, 4, "baseline"))
"""

from .charts_density import cost_by_metro, cost_vs_density
from .charts_economics import cost_decomposition, cumulative_coverage
from .data import (
                   COMPONENTS,
                   CostTableMissingError,
                   available,
                   load,
                   metro_order,
)
from .style import apply_style, audit_overflow, save_figure

__all__ = [
    "COMPONENTS",
    "CostTableMissingError",
    "apply_style",
    "audit_overflow",
    "available",
    "cost_by_metro",
    "cost_decomposition",
    "cost_vs_density",
    "cumulative_coverage",
    "load",
    "metro_order",
    "save_figure",
]
