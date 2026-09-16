"""Subprocess execution with every command recorded.

External tools (routing preprocessing, dbt, archive extraction) are the part
of a pipeline that breaks on someone else's machine. Routing them through
:func:`run` means the exact argv, working directory, exit code, duration and
output tail all land in ``logs/run-*/commands.jsonl``.

    run(["osrm-extract", str(pbf)], cwd=work)          # raises on failure
    res = run(["dbt", "build"], check=False)           # inspect res.code
"""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from . import context, paths
from .http import _scrub
from .logging_setup import get_logger, sink

_log = get_logger("shell")
_cmd_log = sink("commands.jsonl")

# How much of stdout/stderr to keep in the structured record.
_TAIL_CHARS = 4000
# Environment variables never written to a log, even if set on the call.
_REDACT = ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASSWD", "CREDENTIAL")


@dataclass
class Result:
    """Outcome of one command."""
    argv: list[str]
    code: int
    stdout: str
    stderr: str
    seconds: float

    @property
    def ok(self) -> bool:
        """True when the command exited zero."""
        return self.code == 0

    def __str__(self) -> str:
        """One-line summary. Scrubbed, because a Result often gets logged."""
        return f"<{_scrub(shlex.join(self.argv))[:60]} exit={self.code}>"


def _safe_env(extra: dict | None) -> dict | None:
    """Redact anything that looks like a credential before logging."""
    if not extra:
        return None
    return {k: ("<redacted>" if any(s in k.upper() for s in _REDACT) else v)
            for k, v in extra.items()}


def _safe_argv(argv: list[str]) -> list[str]:
    """Argv as it may be written to a log, with credentials removed.

    Redacting only the ``env`` override dict was a half fix. A secret reaches
    a subprocess just as often on the command line — ``--token=...``, an
    ``Authorization: Bearer ...`` header, a presigned URL — and argv is
    written verbatim to commands.jsonl and to console.log by the ``$ %s``
    line. Reusing ``http._scrub`` means there is one definition of what a
    credential looks like rather than two that drift.

    The Result still carries the REAL argv: the command has to run, and a
    caller inspecting the failure needs what was actually invoked.
    """
    return [_scrub(a) for a in argv]


def run(argv: list[str] | str, *, cwd: Path | str | None = None,
        env: dict | None = None, check: bool = True,
        timeout: float | None = None, capture: bool = True) -> Result:
    """Run a command, logging it in full.

    Parameters
    ----------
    argv
        Command as a list (preferred) or a string, which is split with
        ``shlex`` — no shell is ever invoked, so quoting cannot surprise you.
    check
        Raise ``CalledProcessError`` on a non-zero exit. Set False when a
        failure is an expected branch rather than a bug.
    """
    if isinstance(argv, str):
        argv = shlex.split(argv)
    workdir = Path(cwd) if cwd else Path.cwd()
    merged = {**os.environ, **(env or {})}

    safe = _safe_argv(argv)
    pretty = shlex.join(safe)
    _log.info("$ %s", pretty if len(pretty) < 140 else pretty[:137] + "...")

    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            argv, cwd=str(workdir), env=merged, timeout=timeout,
            capture_output=capture, text=True,
        )
        code, out, err = proc.returncode, proc.stdout or "", proc.stderr or ""
    except FileNotFoundError as exc:
        code, out, err = 127, "", f"executable not found: {exc}"
    except subprocess.TimeoutExpired as exc:
        code, out, err = 124, (exc.stdout or ""), f"timed out after {timeout}s"

    dt = time.perf_counter() - t0
    result = Result(argv, code, out, err, dt)

    # Output is scrubbed as well as argv: a tool that echoes its own command
    # line on failure - curl, aws, dbt all do - would otherwise put back
    # exactly what _safe_argv just took out.
    _cmd_log.debug("command", extra={"fields": {
        "event": "command", "argv": safe, "cwd": str(workdir),
        "env_overrides": _safe_env(env), "exit_code": code,
        "seconds": round(dt, 3),
        "stdout_tail": _scrub(out[-_TAIL_CHARS:]),
        "stderr_tail": _scrub(err[-_TAIL_CHARS:]),
        **context.snapshot()}})

    if code == 0:
        _log.debug("exit 0 in %.2fs", dt)
    else:
        _log.error("exit %d in %.2fs | %s", code, dt,
                   _scrub((err.strip().splitlines()
                           or ["<no stderr>"])[-1][:200]))
        if check:
            # The scrubbed argv, not the real one: an uncaught
            # CalledProcessError renders its cmd into the traceback, which
            # lands in errors.log and usually in a CI transcript too.
            raise subprocess.CalledProcessError(code, safe, out, err)
    return result


def which(name: str) -> str | None:
    """Locate an executable, logging whether it was found.

    Used for optional dependencies (OSRM, dbt) so a missing tool degrades to
    a documented fallback rather than an opaque crash.
    """
    from shutil import which as _which
    found = _which(name)
    if found:
        _log.debug("found %s -> %s", name, found)
    else:
        _log.warning("executable %r not on PATH", name)
    return found


def rel(path: Path | str) -> str:
    """Repo-relative path, re-exported so callers need one import."""
    return paths.rel(path)
