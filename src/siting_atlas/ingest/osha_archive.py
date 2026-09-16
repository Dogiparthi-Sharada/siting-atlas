"""Stream the DOL inspection export without unpacking it.

Split out of `osha.py` so that "how do I read a 1.4 GB multi-part zip" and
"which of these establishments is Amazon" are separate problems. The archive
handling is generic to the DOL bulk download; everything in `osha.py` is
about the retailer.
"""

from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path

from ..common.logging_setup import get_logger

_log = get_logger("osha.archive")


def members(path: Path) -> list:
    """Every CSV inside the archive, in order.

    The DOL export is not one file: it arrives as ~105 chunks of about 13 MB
    each, and EVERY chunk repeats the header. Reading only the largest member
    - which is what a single-file reader does - would silently return 1% of
    the data and look like a successful run.
    """
    with zipfile.ZipFile(path) as zf:
        names = sorted(n for n in zf.namelist()
                       if n.lower().endswith((".csv", ".txt")))
    if not names:
        raise ValueError(f"no CSV inside {path.name}")
    return names


def rows(path: Path):
    """Yield (fields, raw_line) across every chunk, skipping repeated headers.

    Streams rather than concatenating: the archive is 1.4 GB compressed and
    we keep well under 0.1% of it.
    """
    if path.suffix.lower() != ".zip":
        with open(path, encoding="utf-8", errors="replace") as fh:
            head = next(csv.reader([next(fh)]))
            for line in fh:
                yield head, line
        return

    names = members(path)
    _log.info("%s: %d chunk(s), %.0f MB compressed", path.name, len(names),
              path.stat().st_size / 1e6)
    with zipfile.ZipFile(path) as zf:
        for i, name in enumerate(names, 1):
            with zf.open(name) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8",
                                        errors="replace")
                head = next(csv.reader([next(text)]))
                for line in text:
                    yield head, line
            if i % 25 == 0:
                _log.info("  ...%d/%d chunks", i, len(names))
