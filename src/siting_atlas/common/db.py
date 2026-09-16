"""DuckDB access with every statement logged.

No module opens its own connection. Going through :func:`connect` means each
statement lands in ``logs/run-*/sql.jsonl`` with its parameters, elapsed time,
row count and calling context — which is the difference between debugging a
pipeline and guessing at one.

    with connect() as db:
        db.execute("CREATE TABLE t AS SELECT * FROM read_parquet(?)", [path])
        df = db.df("SELECT COUNT(*) AS n FROM t")

Slow statements are surfaced on the console; everything else stays in the
file so the terminal remains readable.
"""

from __future__ import annotations

import re
import time
from contextlib import contextmanager
from pathlib import Path

import duckdb

from . import context, paths
from .http import _scrub
from .logging_setup import get_logger, sink

_log = get_logger("db")
_sql_log = sink("sql.jsonl")

# Statements slower than this are promoted to the console at WARNING.
SLOW_QUERY_SECONDS = 2.0
# Console preview length for a statement; the full text always reaches JSONL.
_PREVIEW = 110


def _flatten(sql: str) -> str:
    """Collapse whitespace so a multi-line statement logs as one line."""
    return re.sub(r"\s+", " ", sql).strip()


def _verb(sql: str) -> str:
    """Leading keyword, used to group statements in analysis."""
    m = re.match(r"\s*(\w+)", sql)
    return m.group(1).upper() if m else "?"


#: Parameter types that cannot carry a credential and are therefore written
#: to the log as themselves. Everything else is text, and text is the thing
#: that leaks.
_NOT_A_SECRET = (int, float, bool, type(None))


def _loggable_params(params) -> list | None:
    """Bind parameters as they may safely be written to sql.jsonl.

    A bind parameter is arbitrary caller data on its way into a log file, and
    this project has already written a live EIA_API_KEY into three log files
    at once by logging text it had not scrubbed — which is the reason
    ``http._scrub`` exists at all. Nothing makes a ``params`` list different
    in kind from a URL or an argv: the day a credential arrives as a bind
    value, it lands in sql.jsonl verbatim. "No parameter is a secret today"
    is an observation about the current callers, not a property of this
    function.

    Reusing ``http._scrub`` rather than writing a second redactor is the
    point: HTTP, shell and SQL then share one definition of what a secret
    looks like, so widening it widens all three. Numbers are passed through
    untouched — a number cannot hide a key, and rewriting 7 as "7" would
    silently change the shape of every record in the file.
    """
    if not params:
        return None
    return [p if isinstance(p, _NOT_A_SECRET) else _scrub(p) for p in params]


def _split_statements(sql: str) -> list[str]:
    """Split a script on the semicolons that actually terminate statements.

    A bare ``sql.split(";")`` cuts ``INSERT INTO t VALUES ('a;b')`` in half,
    and would silently change the meaning of any script whose halves both
    happen to parse. So string literals, ``--`` line comments and ``/* */``
    blocks are walked over rather than scanned through.
    """
    out: list[str] = []
    buf: list[str] = []
    i, n = 0, len(sql)
    while i < n:
        ch = sql[i]
        if ch in "'\"":
            buf.append(ch)
            i += 1
            while i < n:
                if sql[i] == ch:
                    # SQL escapes a quote by doubling it: '' stays inside.
                    if i + 1 < n and sql[i + 1] == ch:
                        buf.append(sql[i:i + 2])
                        i += 2
                        continue
                    buf.append(ch)
                    i += 1
                    break
                buf.append(sql[i])
                i += 1
        elif sql.startswith("--", i):
            j = sql.find("\n", i)
            j = n if j < 0 else j
            buf.append(sql[i:j])
            i = j
        elif sql.startswith("/*", i):
            j = sql.find("*/", i + 2)
            j = n if j < 0 else j + 2
            buf.append(sql[i:j])
            i = j
        elif ch == ";":
            out.append("".join(buf))
            buf = []
            i += 1
        else:
            buf.append(ch)
            i += 1
    out.append("".join(buf))
    return [s for s in (p.strip() for p in out) if s]


class LoggedConnection:
    """Thin wrapper around a DuckDB connection that traces every call.

    Only the methods the pipeline actually uses are exposed; anything else
    falls through via ``__getattr__`` so the underlying API stays available.
    """

    def __init__(self, con: duckdb.DuckDBPyConnection, label: str):
        """Wrap a live DuckDB connection. ``label`` is the repo-relative
        database path, carried into every log record so statements from
        two databases in one run stay distinguishable."""
        self._con = con
        self._label = label
        self.statement_count = 0
        self.total_seconds = 0.0

    # -- core ---------------------------------------------------------------
    def _run(self, sql: str, params, kind: str):
        """Execute one statement and record it, whatever the outcome.

        The log write is in a ``finally`` so a failing statement is
        recorded before the exception propagates — the statement that
        broke a run is the one you most need in the file. ``kind`` says
        which wrapper was called (execute/df/scalar/script).
        """
        # Scrub the statement TEXT too, not just its params. Inlining a
        # credential into SQL is bad practice, but "we assumed nobody would"
        # is the same assumption that put a live EIA key in three log files
        # earlier in this project.
        flat = _scrub(_flatten(sql))
        t0 = time.perf_counter()
        error = None
        try:
            rel = (self._con.execute(sql, params) if params is not None
                   else self._con.execute(sql))
            return rel
        except Exception as exc:                      # log then re-raise
            error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            dt = time.perf_counter() - t0
            self.statement_count += 1
            self.total_seconds += dt
            ctx = context.snapshot()
            _sql_log.debug(
                "sql",
                extra={"fields": {
                    "event": "sql", "kind": kind, "verb": _verb(flat),
                    "db": self._label, "sql": flat,
                    "params": _loggable_params(params),
                    "seconds": round(dt, 4), "error": error, **ctx}})
            if error:
                _log.error("SQL failed (%.2fs) %s | %s", dt,
                           flat[:_PREVIEW], error)
            elif dt >= SLOW_QUERY_SECONDS:
                _log.warning("slow SQL %.2fs | %s", dt, flat[:_PREVIEW])
            else:
                _log.debug("sql %.3fs | %s", dt, flat[:_PREVIEW])

    def execute(self, sql: str, params=None):
        """Run a statement. Returns the DuckDB relation."""
        return self._run(sql, params, "execute")

    def df(self, sql: str, params=None):
        """Run a query and return a pandas DataFrame, logging the row count."""
        rel = self._run(sql, params, "df")
        out = rel.df()
        _sql_log.debug("sql_result",
                       extra={"fields": {"event": "sql_result",
                                         "rows": len(out),
                                         "cols": list(out.columns),
                                         **context.snapshot()}})
        return out

    def scalar(self, sql: str, params=None):
        """Run a query expected to yield exactly one value."""
        row = self._run(sql, params, "scalar").fetchone()
        return row[0] if row else None

    def script(self, sql: str) -> int:
        """Execute a semicolon-separated script, statement by statement, so
        that a failure names the statement that broke rather than the file.

        Returns the number of statements run. The split is literal- and
        comment-aware; see :func:`_split_statements` for why a bare
        ``split(';')`` is not good enough.
        """
        stmts = _split_statements(sql)
        for s in stmts:
            self._run(s, None, "script")
        return len(stmts)

    def __getattr__(self, item):
        """Fall through to the raw DuckDB connection.

        Only reached for attributes this wrapper does not define, so the
        full DuckDB API stays reachable — but note that anything used
        this way bypasses the SQL log, which is the point of the class.
        """
        return getattr(self._con, item)


@contextmanager
def connect(path: Path | str | None = None, read_only: bool = False):
    """Open the warehouse (or an in-memory database when ``path`` is None).

    Logs open and close, and reports how many statements the session ran —
    a cheap way to notice a stage doing far more work than expected.
    """
    target = Path(path) if path else paths.WAREHOUSE
    if path is None:
        target.parent.mkdir(parents=True, exist_ok=True)
    label = paths.rel(target)

    _log.debug("open warehouse %s (read_only=%s)", label, read_only)
    con = duckdb.connect(str(target), read_only=read_only)
    wrapper = LoggedConnection(con, label)
    t0 = time.perf_counter()
    try:
        yield wrapper
    finally:
        con.close()
        _log.debug(
            "closed %s | %d statements in %.2fs (session %.2fs)",
            label, wrapper.statement_count, wrapper.total_seconds,
            time.perf_counter() - t0,
            extra={"fields": {"event": "db_close", "db": label,
                              "statements": wrapper.statement_count,
                              "sql_seconds": round(wrapper.total_seconds, 3)}})


@contextmanager
def memory():
    """In-memory database, for tests and for reading parquet without a file."""
    con = duckdb.connect(":memory:")
    wrapper = LoggedConnection(con, ":memory:")
    try:
        yield wrapper
    finally:
        con.close()
