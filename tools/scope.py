"""Measured scope figures, for documents and figures to quote.

Reads ``outputs/metrics/scope.json``, written by
``python -m siting_atlas.report.scope``. Stdlib only, deliberately: the docx
and pptx builders run under a different interpreter from the pipeline, so this
must not import the package.

Use it instead of typing a number:

    from scope import SCOPE
    SCOPE.zctas          # 2413
    SCOPE.zctas_label    # '2,413'
    SCOPE.capital        # '$7.2B-$12.1B'

The proposal previously quoted "approximately 5,200 ZCTAs" in nine places. The
measured figure is 2,413. The estimate was never wrong on purpose — it was
typed once, copied, and never re-checked. Deriving it removes the possibility.
"""

from __future__ import annotations

import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SCOPE_JSON = _REPO / "outputs" / "metrics" / "scope.json"


class Scope:
    """Read-only view of the measured scope figures."""

    def __init__(self, path: Path = _SCOPE_JSON):
        """Load the measured scope figures, or fail naming the command.

        Failing at construction is deliberate: SCOPE is built at import, so a
        document build stops before it can render a placeholder where a
        headline number should be.
        """
        if not path.exists():
            raise FileNotFoundError(
                f"{path} is missing. Every scope figure quoted in the "
                f"proposal is derived from it rather than typed, so build it "
                f"first:\n\n"
                f"    PYTHONPATH=src python -m siting_atlas.report.scope\n")
        self._d = json.loads(path.read_text(encoding="utf-8"))
        self._pilot = self._d["pilot"]
        self._capital = self._d["capital"]
        self._compute = self._d["compute"]

    # -- pilot -----------------------------------------------------------
    @property
    def zctas(self) -> int:
        """Measured ZCTA count in the pilot metros."""
        return self._pilot["zctas"]

    @property
    def zctas_label(self) -> str:
        """ZCTA count with thousands separators, e.g. '2,413'."""
        return f"{self.zctas:,}"

    @property
    def counties(self) -> int:
        """Counties constituting the pilot, per the OMB delineation."""
        return self._pilot["counties"]

    @property
    def metros(self) -> int:
        """Number of pilot metros, composites counted once."""
        return self._pilot["metros"]

    @property
    def metros_fit(self) -> int:
        """Metros the model may be fitted on."""
        return self._pilot["metros_fit"]

    @property
    def metros_heldout(self) -> int:
        """Metros reserved for the geographic transfer test."""
        return self._pilot["metros_heldout"]

    @property
    def by_metro(self) -> dict:
        """ZCTA count per metro label, largest first."""
        return dict(self._pilot["zctas_by_metro"])

    @property
    def definition(self) -> str:
        """Which delineation defined the pilot, for a figure caption."""
        return self._pilot["definition"]

    @property
    def national_zctas_label(self) -> str:
        """ZCTAs nationally, formatted, for the 'if scaled' comparison."""
        return f"{self._d['national_zctas']:,}"

    # -- derived headline figures ----------------------------------------
    @property
    def capital(self) -> str:
        """e.g. '$7.2B-$12.1B' — ZCTAs x capital per activation."""
        return self._capital["label"]

    @property
    def capital_national(self) -> str:
        """Capital at risk if the method were run nationally."""
        return self._capital["national_label"]

    @property
    def per_activation(self) -> str:
        """Capital per activation as a range label, e.g. '$3-5M'."""
        lo, hi = self._capital["per_activation_usd"]
        return f"${lo / 1e6:.0f}-{hi / 1e6:.0f}M"

    @property
    def draws(self) -> str:
        """e.g. '24 billion' uncertainty draws."""
        return self._compute["label"]

    @property
    def search_space(self) -> str:
        """e.g. '2^2,413' candidate portfolios."""
        return self._compute["search_space_label"]

    # -- panel -----------------------------------------------------------
    @property
    def panel_rows_label(self) -> str:
        """Panel row count, or 'unbuilt' if L3 has not been run."""
        return self._d.get("panel", {}).get("rows_label", "unbuilt")

    @property
    def panel_mb(self) -> float:
        """Panel size on disk in megabytes; 0.0 if it does not exist."""
        return self._d.get("panel", {}).get("megabytes", 0.0)


#: Import this. Constructed at import so a missing artefact fails the build
#: loudly rather than rendering a document with a placeholder in it.
SCOPE = Scope()
