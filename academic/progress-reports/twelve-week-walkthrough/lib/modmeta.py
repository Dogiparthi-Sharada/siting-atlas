"""Mode constants and formatters the module entries share.

Its own file because ``spec`` imports both module lists and both module
lists need these, so putting them in ``spec`` would make an import cycle.
"""

from __future__ import annotations

#: ``run_week.sh nn`` re-derives this result offline from the clone. The
#: number on the page is demonstrated, not merely reported.
RECOMPUTE = "RECOMPUTE"

#: ``run_week.sh nn`` reads a shipped artefact and recomputes nothing,
#: because the stage needs the raw cache, three API keys, ~4 GB of
#: downloads, or ninety minutes of CPU. Legitimate, but the reader is told
#: rather than left to assume.
INSPECT = "INSPECT"


def pct(x: float) -> str:
    return f"{x:.2%}"


def usd(x: float, dp: int = 4) -> str:
    return f"${x:.{dp}f}"
