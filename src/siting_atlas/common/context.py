"""Ambient run context: who is running, which layer, which stage.

Every log record, SQL statement, shell command and HTTP request is stamped
with this context, so a line in any log file can be traced back to the exact
pipeline position that produced it.

Context is held in ``contextvars`` rather than globals so it stays correct
under asyncio: each task gets its own copy, and a stage running concurrently
with another cannot overwrite its layer stamp.

Note the limit, because the word "concurrent" hides it. A ``threading.Thread``
does NOT inherit the caller's context — it starts from the defaults, so a
threaded stage would log ``layer="--"`` rather than the layer it ran under.
Nothing in this pipeline threads, so this is a boundary to know about rather
than a bug to work around; if a stage ever does spawn threads, pass the
context in explicitly with ``contextvars.copy_context().run(...)``.

    with layer("L1"), stage("normalise:acs"):
        ...                     # every event here carries L1 / normalise:acs
"""

from __future__ import annotations

import os
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime

# --- pipeline layers, from HANDBOOK_07_ENGINEERING --------------------------
LAYERS = {
    "L0": "acquire",        # network -> immutable cache
    "L1": "normalise",      # cache -> typed parquet
    "L2": "warehouse",      # parquet -> DuckDB star schema
    "L3": "feature",        # warehouse -> the single model panel
    "L4": "model",          # panel -> estimates
    "L5": "report",         # estimates -> figures, tables, metrics
    "--": "setup",          # bootstrap, config, anything pre-pipeline
}

_run_id: ContextVar[str] = ContextVar("run_id", default="")
_layer: ContextVar[str] = ContextVar("layer", default="--")
_stage: ContextVar[str] = ContextVar("stage", default="")


def new_run_id() -> str:
    """Short, sortable, unique identifier for one execution of the pipeline.

    Format ``YYYYmmdd-HHMMSS-xxxx``. The timestamp makes log directories sort
    chronologically; the suffix disambiguates runs started in the same second.
    """
    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"{ts}-{uuid.uuid4().hex[:4]}"


def init_run(run_id: str | None = None) -> str:
    """Start (or adopt) a run. Honours SITING_ATLAS_RUN_ID so that a shell
    script can correlate several Python invocations into one logical run."""
    rid = run_id or os.environ.get("SITING_ATLAS_RUN_ID") or new_run_id()
    _run_id.set(rid)
    os.environ["SITING_ATLAS_RUN_ID"] = rid
    return rid


def run_id() -> str:
    """This run's id, starting a run if no entry point has yet.

    Self-initialising so a library call or a test can log before any
    main() has run, rather than emitting records stamped with "".
    """
    return _run_id.get() or init_run()


def current_layer() -> str:
    """Pipeline layer code (L0..L5) currently in scope, else "--"."""
    return _layer.get()


def current_stage() -> str:
    """Name of the step currently in scope, or "" outside one."""
    return _stage.get()


def snapshot() -> dict:
    """The context fields attached to every structured log record."""
    lyr = _layer.get()
    return {
        "run_id": run_id(),
        "layer": lyr,
        "layer_name": LAYERS.get(lyr, "unknown"),
        "stage": _stage.get(),
    }


@contextmanager
def layer(code: str):
    """Enter a pipeline layer. ``code`` must be one of LAYERS."""
    if code not in LAYERS:
        raise ValueError(
            f"unknown layer {code!r}; expected one of {sorted(LAYERS)}"
        )
    token = _layer.set(code)
    try:
        yield code
    finally:
        _layer.reset(token)


@contextmanager
def stage(name: str):
    """Enter a named step inside a layer, e.g. ``normalise:acs``."""
    token = _stage.set(name)
    try:
        yield name
    finally:
        _stage.reset(token)
