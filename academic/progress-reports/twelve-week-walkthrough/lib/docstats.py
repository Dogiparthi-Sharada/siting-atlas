"""Counts read out of the repository's markdown at build time.

Weeks 1, 2 and 10 are about DECISIONS rather than about results, and a
decision leaves no metrics artefact behind. The evidence for "we considered
five options and rejected four" is `docs/ALTERNATIVES.md` itself.

So those weeks count patterns in the documents instead of reading JSON.
Same rule either way, which is the point: a number on a page is derived
from a file in the repository at the moment the page is built, never typed
into the spec. Add an option to ALTERNATIVES.md and week 2's count moves
without anyone editing the walkthrough.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import repo


def _read(rel: str) -> str | None:
    try:
        with open(repo.path(rel), encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def count(rel: str, pattern: str, *, flags: int = re.M) -> int:
    """How many times ``pattern`` matches in a repository document.

    Returns -1 rather than raising when the file is missing, so one moved
    document degrades a single row instead of taking the whole build down.
    A -1 on a page is visibly wrong, which is the intent -- it should be
    noticed and fixed, not silently rendered as a plausible zero.
    """
    text = _read(rel)
    if text is None:
        return -1
    return len(re.findall(pattern, text, flags))


def lines(rel: str) -> int:
    """Length of a document, for "we wrote this much down" claims."""
    text = _read(rel)
    return -1 if text is None else len(text.splitlines())


def exists(rel: str) -> bool:
    return os.path.exists(repo.path(rel))
