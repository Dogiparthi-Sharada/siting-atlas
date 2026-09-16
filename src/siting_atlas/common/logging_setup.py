"""Logging configuration: one human stream, several machine streams.

Design
------
Console  a compact, coloured line for a person watching the run.
Files    written under ``logs/run-<run_id>/`` and segregated by concern, so
         that debugging a bad query does not mean scrolling past HTTP noise:

    console.log    everything, plain text, exactly as printed
    events.jsonl   every log record as structured JSON
    sql.jsonl      one record per SQL statement (see common.db)
    commands.jsonl one record per shell command (see common.shell)
    http.jsonl     one record per HTTP request (see common.http)
    errors.log     WARNING and above only, for a fast post-mortem

Levels are standard. Set ``SITING_ATLAS_LOG_LEVEL=DEBUG`` for full detail;
console defaults to INFO while the files always capture DEBUG, so a failure
can be diagnosed from the artefacts without re-running.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from . import context, paths

CONSOLE_FMT = ("%(asctime)s %(levelname).1s %(layer)-3s %(short)-22s "
               "%(message)s")
DATE_FMT = "%H:%M:%S"

_COLOUR = {
    "DEBUG": "\033[2m", "INFO": "", "WARNING": "\033[33m",
    "ERROR": "\033[31m", "CRITICAL": "\033[1;31m",
}
_RESET = "\033[0m"
_configured = False
_log_dir: Path | None = None


class ContextFilter(logging.Filter):
    """Stamp every record with run/layer/stage so no line is orphaned."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Attach the ambient context and always keep the record.

        Returns True unconditionally: this is a Filter used for its side
        effect, which is the documented way to enrich a record.
        """
        ctx = context.snapshot()
        record.run_id = ctx["run_id"]
        record.layer = ctx["layer"]
        record.layer_name = ctx["layer_name"]
        record.stage = ctx["stage"]
        # A short, fixed-width origin for the console: prefer the stage name,
        # fall back to the module that emitted the record.
        record.short = ctx["stage"] or record.name.split(".")[-1]
        return True


class ColourFormatter(logging.Formatter):
    """Console formatter; colour only when attached to a terminal."""

    def __init__(self, use_colour: bool):
        """Build the console formatter. ``use_colour`` is normally
        ``sys.stdout.isatty()`` — escape codes in a redirected log or a CI
        transcript are noise, not colour."""
        super().__init__(CONSOLE_FMT, DATE_FMT)
        self.use_colour = use_colour

    def format(self, record: logging.LogRecord) -> str:
        """Format the record, wrapping it in a level colour on a TTY."""
        line = super().format(record)
        if self.use_colour:
            prefix = _COLOUR.get(record.levelname, "")
            if prefix:
                line = f"{prefix}{line}{_RESET}"
        return line


class JsonlFormatter(logging.Formatter):
    """One JSON object per line. Stable key order for readable diffs."""

    def format(self, record: logging.LogRecord) -> str:
        """Render the record as one JSON object.

        Anything passed as ``extra={"fields": {...}}`` is nested under
        "fields" rather than flattened, so a caller cannot shadow a
        reserved key like "level" or "run_id".
        """
        payload = {
            "ts": datetime.fromtimestamp(
                record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "run_id": getattr(record, "run_id", ""),
            "layer": getattr(record, "layer", ""),
            "stage": getattr(record, "stage", ""),
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Anything passed via logger.info(..., extra={"fields": {...}})
        extra = getattr(record, "fields", None)
        if extra:
            payload["fields"] = extra
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def log_dir() -> Path:
    """Directory holding this run's logs. Created on first use."""
    global _log_dir
    if _log_dir is None:
        _log_dir = paths.ROOT / "logs" / f"run-{context.run_id()}"
        _log_dir.mkdir(parents=True, exist_ok=True)
    return _log_dir


def _file_handler(name: str, level: int, fmt: logging.Formatter):
    """One file handler: level, formatter and the context stamp.

    Every handler needs its own ContextFilter instance — a filter is
    attached per handler, not globally, so a shared one would leave
    whichever stream was configured last without run/layer fields.
    """
    h = logging.FileHandler(log_dir() / name, encoding="utf-8")
    h.setLevel(level)
    h.setFormatter(fmt)
    h.addFilter(ContextFilter())
    return h


def configure(level: str | None = None, quiet: bool = False) -> Path:
    """Install handlers. Idempotent — safe to call from any entry point.

    Returns the directory the logs are being written to.
    """
    global _configured
    if _configured:
        return log_dir()

    context.run_id()                       # materialise the id before use
    console_level = getattr(
        logging,
        (level or os.environ.get("SITING_ATLAS_LOG_LEVEL", "INFO")).upper(),
        logging.INFO,
    )

    root = logging.getLogger("siting_atlas")
    root.setLevel(logging.DEBUG)           # files capture everything
    root.handlers.clear()
    root.propagate = False

    if not quiet:
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(console_level)
        console.setFormatter(ColourFormatter(sys.stdout.isatty()))
        console.addFilter(ContextFilter())
        root.addHandler(console)

    plain = logging.Formatter(CONSOLE_FMT, DATE_FMT)
    root.addHandler(_file_handler("console.log", logging.DEBUG, plain))
    root.addHandler(_file_handler("events.jsonl", logging.DEBUG,
                                  JsonlFormatter()))
    root.addHandler(_file_handler("errors.log", logging.WARNING, plain))

    _configured = True
    logging.getLogger("siting_atlas.setup").info(
        "run %s | logs -> %s", context.run_id(), paths.rel(log_dir())
    )
    return log_dir()


def get_logger(name: str) -> logging.Logger:
    """Child logger. Call ``configure()`` first from the entry point."""
    return logging.getLogger(f"siting_atlas.{name}")


def sink(filename: str) -> logging.Logger:
    """A dedicated JSONL logger that does NOT go to the console.

    Used for the high-volume streams (SQL, commands, HTTP) so the terminal
    stays readable while the artefacts stay complete.
    """
    name = f"siting_atlas.sink.{Path(filename).stem}"
    lg = logging.getLogger(name)
    if lg.handlers:
        return lg
    lg.setLevel(logging.DEBUG)
    lg.propagate = False                   # keep it out of console.log
    lg.addHandler(_file_handler(filename, logging.DEBUG, JsonlFormatter()))
    return lg
