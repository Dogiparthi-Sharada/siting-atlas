"""Stage-by-stage artefact writing, so an interruption costs one stage.

The artefact is rewritten in full after every stage rather than once at the
end. A previous run of a comparable job lost 45 minutes of correct work by
writing only on completion, and the cost of avoiding that is a few
milliseconds of JSON serialisation per stage.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from ..common import paths
from ..common.logging_setup import get_logger

_log = get_logger("models.metro_artefact")

__all__ = ["plain", "write", "done", "coverage_ok"]


def plain(o):
    """JSON encoder hook for the numpy scalars pandas hands back."""
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    raise TypeError(type(o))


def write(doc: dict, target: Path) -> None:
    paths.ensure_dirs()
    doc["written_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    target.write_text(json.dumps(doc, indent=1, default=plain) + "\n")
    _log.info("artefact -> %s (%d stages)", paths.rel(target),
              len(doc.get("stages_complete", [])))


def done(doc: dict, name: str, target: Path) -> None:
    doc.setdefault("stages_complete", []).append(name)
    write(doc, target)


def coverage_ok(frame: pd.DataFrame, col: str, years, floor: float) -> bool:
    """True if `col` is present on >= `floor` of metro-years in EVERY year.

    Every year, not on average. A column that is 98% present in the last
    three years and 24% present in the first four -- which is exactly what
    the Census permits ingest looks like -- would pass an average test and
    then quietly restrict the fit to a quarter of the universe in the years
    that matter most.
    """
    cov = frame[frame["year"].isin(years)].groupby("year")[col].apply(
        lambda s: s.notna().mean())
    return bool((cov >= floor).all())
