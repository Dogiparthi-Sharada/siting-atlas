"""Tracing helpers: layer entry/exit, timed steps, and artefact recording.

The point of this module is that crossing a pipeline boundary is never
implicit. Entering L1 logs it; leaving L1 logs the elapsed time and whatever
the layer produced. A failed run therefore shows exactly how far it got.

    with traced_layer("L1", "normalise sources"):
        with step("acs"):
            ...
            artefact(path, rows=len(df))
"""

from __future__ import annotations

import functools
import time
import traceback
from contextlib import contextmanager
from pathlib import Path

from . import context, paths
from .logging_setup import get_logger

_log = get_logger("trace")


def _size(path: Path) -> str:
    """Human-readable file size, or "?" if the file cannot be stat'd.

    Never raises: this is called while recording an artefact, and a
    logging helper must not be able to abort the stage it is logging.
    """
    try:
        n = path.stat().st_size
    except OSError:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}GB"


@contextmanager
def traced_layer(code: str, detail: str = ""):
    """Enter a pipeline layer, logging the crossing on both sides."""
    name = context.LAYERS.get(code, "?")
    with context.layer(code):
        _log.info("=> ENTER %s (%s)%s", code, name,
                  f" - {detail}" if detail else "",
                  extra={"fields": {"event": "layer_enter", "layer": code}})
        t0 = time.perf_counter()
        try:
            yield code
        except Exception as exc:
            dt = time.perf_counter() - t0
            _log.error("<= ABORT %s (%s) after %.2fs: %s", code, name, dt,
                       exc, extra={"fields": {
                           "event": "layer_abort", "layer": code,
                           "seconds": round(dt, 3),
                           "error": f"{type(exc).__name__}: {exc}",
                           "traceback": traceback.format_exc()}})
            raise
        else:
            dt = time.perf_counter() - t0
            _log.info("<= LEAVE %s (%s) in %.2fs", code, name, dt,
                      extra={"fields": {"event": "layer_leave",
                                        "layer": code,
                                        "seconds": round(dt, 3)}})


@contextmanager
def step(name: str, **fields):
    """A named unit of work inside a layer. Times it and records failures."""
    with context.stage(name):
        _log.debug("step start", extra={"fields": {"event": "step_start",
                                                   "step": name, **fields}})
        t0 = time.perf_counter()
        try:
            yield
        except Exception as exc:
            dt = time.perf_counter() - t0
            _log.error("step FAILED after %.2fs: %s", dt, exc,
                       extra={"fields": {
                           "event": "step_fail", "step": name,
                           "seconds": round(dt, 3),
                           "error": f"{type(exc).__name__}: {exc}",
                           "traceback": traceback.format_exc(), **fields}})
            raise
        else:
            dt = time.perf_counter() - t0
            _log.info("done in %.2fs", dt,
                      extra={"fields": {"event": "step_ok", "step": name,
                                        "seconds": round(dt, 3), **fields}})


def traced(layer_code: str | None = None):
    """Decorator form of :func:`step`, using the function name as the step.

        @traced("L1")
        def normalise_acs(...): ...
    """
    def decorator(fn):
        """Bind the tracing wrapper to one function."""
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            """Run fn inside a step, and inside a layer if one was given."""
            if layer_code:
                with context.layer(layer_code), step(fn.__name__):
                    return fn(*args, **kwargs)
            with step(fn.__name__):
                return fn(*args, **kwargs)
        return wrapper
    return decorator


def artefact(path: Path | str, **fields) -> None:
    """Record that a stage produced a file. Shows up in events.jsonl so a
    run can be audited for what it actually wrote."""
    p = Path(path)
    _log.info("wrote %s (%s)%s", paths.rel(p), _size(p),
              "".join(f" {k}={v}" for k, v in fields.items()),
              extra={"fields": {"event": "artefact", "path": str(p),
                                "bytes": p.stat().st_size if p.exists() else 0,
                                **fields}})


def metric(name: str, value, **fields) -> None:
    """Record a single measured quantity (AUC, row count, coverage...)."""
    _log.info("%-30s %s", name, value,
              extra={"fields": {"event": "metric", "name": name,
                                "value": value, **fields}})


def checkpoint(message: str, **fields) -> None:
    """A named point of interest, for reconstructing control flow later."""
    _log.debug(message, extra={"fields": {"event": "checkpoint", **fields}})
