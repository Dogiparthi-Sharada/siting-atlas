"""Where the siting-atlas clone is. One answer, imported by everyone.

Both the renderer and the document-statistics helper need the repository
path, and having each work it out separately is how two copies of a path
drift apart. ``SITING_ATLAS`` in the environment overrides discovery, for a
clone kept somewhere other than inside ``MSBA_Project``.
"""

from __future__ import annotations

import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_WALKTHROUGH = os.path.abspath(os.path.join(_HERE, ".."))

#: ``.../MSBA_Project/academic/progress-reports/twelve-week-walkthrough``
#: is three levels below ``MSBA_Project``, which holds ``siting-atlas``.
_DEFAULT = os.path.abspath(
    os.path.join(_WALKTHROUGH, "..", "..", "..", "siting-atlas"))

REPO = os.environ.get("SITING_ATLAS", _DEFAULT)
ROOT = _WALKTHROUGH


def path(rel: str) -> str:
    """Absolute path to something inside the repository."""
    return os.path.join(REPO, rel)
