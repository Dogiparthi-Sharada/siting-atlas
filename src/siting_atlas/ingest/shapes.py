"""Shared readers for the shapes publishers actually ship.

`_zpad` is the single most important function in L1 and the reason this file
exists separately: every geographic code in this project is a zero-padded
STRING, always. As an integer `01890` becomes `1890` and every join
downstream silently loses those rows — no error, no warning, just a smaller
answer.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd


def _zpad(series: pd.Series, width: int = 5) -> pd.Series:
    """Zero-padded string codes. The single most important rule in L1."""
    return series.astype(str).str.strip().str.zfill(width)


def _latest(folder: Path, *patterns: str) -> Path | None:
    """First pattern that matches anything, then its LARGEST file.

    The name says "latest" and the tie-break is size, which is deliberate and
    worth stating: a re-download that was interrupted leaves a short file
    next to the good one, and it is usually the newer of the two. Size picks
    the complete download; mtime would pick the truncated one and every
    downstream row count would quietly drop.

    Returns None when no pattern matches, so the caller can raise with a
    message naming what to go and fetch.
    """
    for pattern in patterns:
        hits = [h for h in sorted(folder.glob(pattern))
                if h.name.upper() != "TEMPLATE.CSV"]
        if hits:
            return max(hits, key=lambda p: p.stat().st_size)
    return None


def _member(archive: Path, suffix: str = ".txt") -> bytes:
    """Read the first matching member of a zip without extracting to disk."""
    with zipfile.ZipFile(archive) as zf:
        name = next(n for n in zf.namelist() if n.lower().endswith(suffix))
        return zf.read(name)


# ---------------------------------------------------------------------------
# individual sources
# ---------------------------------------------------------------------------
