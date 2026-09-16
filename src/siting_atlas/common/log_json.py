"""Small JSON helpers used by stages that emit metric files.

Kept separate from logging_setup so that writing a result artefact does not
drag in handler configuration.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from . import context


def write_json(path: Path | str, payload: dict, *, indent: int = 2) -> Path:
    """Write a result artefact, stamped with the run that produced it."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # A stamp describes the WRITE, never the payload. Emitters that resume by
    # reading their own artefact back in (covariate_harness.load does exactly
    # this) carry the previous run's stamps inside `payload`; spreading it last
    # let them shadow the fresh ones, so a resumed run inherited the earlier
    # run's id AND its first-write timestamp, permanently. Two materially
    # different versions of covariate_search.json shipped under one stamp
    # before this was caught on 2026-09-15.
    stamps = ("run_id", "written_at")
    body = {
        "run_id": context.run_id(),
        "written_at": datetime.now(UTC).isoformat(timespec="seconds"),
        **{k: v for k, v in payload.items() if k not in stamps},
    }
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(body, fh, indent=indent, default=str)
    return p


def read_json(path: Path | str) -> dict:
    """Read back an artefact written by :func:`write_json`.

    Deliberately unguarded: a missing or malformed metrics file is a broken
    pipeline, and the caller should see the real exception rather than an
    empty dict that silently reports zero of everything.
    """
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)
