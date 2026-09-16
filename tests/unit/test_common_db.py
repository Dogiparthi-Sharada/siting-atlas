"""LoggedConnection: the audit trail only exists if every statement reaches it.

The module's claim is that sql.jsonl is "the difference between debugging a
pipeline and guessing at one". Two things break that claim silently:

  * a statement that returns before the logging call — the record is simply
    absent, and an absent record looks identical to a statement that was
    never run;
  * a FAILING statement that raises before logging — which is the one you
    most need, and the one you lose exactly when the pipeline breaks.

Records are captured off the real sink logger rather than read from disk, so
the tests exercise the production code path without touching logs/.
"""

from __future__ import annotations

import logging

import duckdb
import pytest

from siting_atlas.common import context
from siting_atlas.common.db import LoggedConnection, connect, memory


class Capture(logging.Handler):
    """Collect the structured `fields` payload of every sink record."""

    def __init__(self):
        super().__init__(logging.DEBUG)
        self.records: list[dict] = []

    def emit(self, record):
        fields = getattr(record, "fields", None)
        if fields is not None:
            self.records.append(fields)

    def of(self, event: str) -> list[dict]:
        return [r for r in self.records if r.get("event") == event]


@pytest.fixture
def sql_log():
    handler = Capture()
    logger = logging.getLogger("siting_atlas.sink.sql")
    logger.addHandler(handler)
    try:
        yield handler
    finally:
        logger.removeHandler(handler)


@pytest.fixture
def db():
    with memory() as connection:
        yield connection


# ---------------------------------------------------------------------------
# every statement is logged
# ---------------------------------------------------------------------------
def test_execute_logs_the_statement_its_verb_and_its_timing(db, sql_log):
    db.execute("CREATE TABLE t AS SELECT 1 AS a")
    (rec,) = sql_log.of("sql")
    assert rec["verb"] == "CREATE"
    assert rec["kind"] == "execute"
    assert rec["sql"] == "CREATE TABLE t AS SELECT 1 AS a"
    assert rec["error"] is None
    assert rec["seconds"] >= 0.0


def test_a_multiline_statement_is_flattened_to_one_log_line(db, sql_log):
    # A newline inside a JSONL value is legal but makes the file unreadable
    # with grep, which is how it is actually read.
    db.execute("SELECT\n    1 AS a,\n    2 AS b")
    assert sql_log.of("sql")[0]["sql"] == "SELECT 1 AS a, 2 AS b"
    assert "\n" not in sql_log.of("sql")[0]["sql"]


def test_parameters_are_recorded_alongside_the_statement(db, sql_log):
    db.execute("SELECT ? AS a, ? AS b", [7, "x"])
    assert sql_log.of("sql")[0]["params"] == [7, "x"]


def test_the_record_carries_the_run_layer_and_stage(db, sql_log):
    context.init_run("20240101-000000-abcd")
    with context.layer("L2"), context.stage("build:dim_zcta"):
        db.execute("SELECT 1")
    rec = sql_log.of("sql")[0]
    assert (rec["run_id"], rec["layer"], rec["stage"]) == (
        "20240101-000000-abcd", "L2", "build:dim_zcta")


def test_df_logs_the_shape_of_what_came_back(db, sql_log):
    frame = db.df("SELECT 1 AS a, 'x' AS b UNION ALL SELECT 2, 'y'")
    assert len(frame) == 2
    (result,) = sql_log.of("sql_result")
    assert result["rows"] == 2
    assert result["cols"] == ["a", "b"]


# ---------------------------------------------------------------------------
# the failure path
# ---------------------------------------------------------------------------
def test_a_failing_statement_is_logged_and_then_re_raised(db, sql_log):
    with pytest.raises(duckdb.Error):
        db.execute("SELECT * FROM table_that_does_not_exist")

    (rec,) = sql_log.of("sql")
    assert rec["error"] is not None, (
        "the failing statement is the one you need in the log")
    assert "table_that_does_not_exist" in rec["sql"]
    assert "CatalogException" in rec["error"] or "Error" in rec["error"]


def test_a_failing_statement_still_counts_towards_the_session_total(db):
    before = db.statement_count
    with pytest.raises(duckdb.Error):
        db.execute("NOT SQL AT ALL")
    assert db.statement_count == before + 1
    assert db.total_seconds >= 0.0


def test_a_failure_inside_script_names_the_statement_not_the_file(db,
                                                                  sql_log):
    with pytest.raises(duckdb.Error):
        db.script("CREATE TABLE ok (a INT); SELECT * FROM missing_table;")
    logged = sql_log.of("sql")
    assert len(logged) == 2, "the good statement ran and was logged first"
    assert logged[0]["error"] is None
    assert "missing_table" in logged[1]["sql"]


# ---------------------------------------------------------------------------
# the thin API
# ---------------------------------------------------------------------------
def test_script_runs_each_statement_and_returns_the_count(db):
    n = db.script("CREATE TABLE t (a INT); INSERT INTO t VALUES (1); "
                  "INSERT INTO t VALUES (2);")
    assert n == 3
    assert db.scalar("SELECT COUNT(*) FROM t") == 2


def test_scalar_returns_none_for_an_empty_result_set(db):
    # A ValueError or an IndexError here would crash a coverage report on an
    # empty table; None is the answer the callers check for.
    assert db.scalar("SELECT 1 WHERE false") is None
    assert db.scalar("SELECT 42") == 42


def test_unwrapped_duckdb_methods_still_work(db):
    # __getattr__ passthrough — the pipeline uses register()/sql() directly.
    db.execute("CREATE TABLE t AS SELECT 1 AS a")
    assert db.sql("SELECT a FROM t").fetchone() == (1,)


def test_statement_count_tracks_every_kind_of_call(db):
    db.execute("CREATE TABLE t AS SELECT 1 AS a")
    db.df("SELECT * FROM t")
    db.scalar("SELECT COUNT(*) FROM t")
    db.script("SELECT 1; SELECT 2")
    assert db.statement_count == 5


def test_connect_creates_the_parent_directory_and_closes_the_file(tmp_path):
    target = tmp_path / "nested" / "wh.duckdb"
    target.parent.mkdir(parents=True)
    with connect(target) as handle:
        handle.execute("CREATE TABLE t AS SELECT 1 AS a")
        assert handle.statement_count == 1
    assert target.exists()
    # If the connection were left open, a second writer would fail — which is
    # what happens when a stage forgets the context manager.
    with connect(target, read_only=True) as handle:
        assert handle.scalar("SELECT COUNT(*) FROM t") == 1


def test_the_connection_closes_even_when_the_body_raises(tmp_path):
    target = tmp_path / "wh.duckdb"
    with pytest.raises(RuntimeError), connect(target) as handle:
        handle.execute("CREATE TABLE t AS SELECT 1 AS a")
        raise RuntimeError("stage failed")
    with connect(target, read_only=True) as handle:
        assert handle.scalar("SELECT COUNT(*) FROM t") == 1


def test_verb_extraction_groups_statements(db, sql_log):
    for sql in ("SELECT 1", "  select 2", "\n\nCREATE TABLE z (a INT)"):
        db.execute(sql)
    assert [r["verb"] for r in sql_log.of("sql")] == ["SELECT", "SELECT",
                                                      "CREATE"]


def test_script_does_not_split_inside_a_string_literal(db):
    # Was an xfail: script() split on a bare ';', cutting a statement in half
    # whenever one appeared inside a string literal or a comment. It now uses
    # db._split_statements, which walks over literals, -- lines and /* */.
    db.execute("CREATE TABLE t (s VARCHAR)")
    db.script("INSERT INTO t VALUES ('a;b'); INSERT INTO t VALUES ('c')")
    assert db.scalar("SELECT COUNT(*) FROM t") == 2


def test_logged_connection_wraps_rather_than_subclasses():
    # A subclass would inherit every duckdb method unlogged; the wrapper is
    # what guarantees execute/df/scalar all go through _run.
    raw = duckdb.connect(":memory:")
    try:
        wrapper = LoggedConnection(raw, ":memory:")
        assert not isinstance(wrapper, duckdb.DuckDBPyConnection)
        assert wrapper._con is raw
    finally:
        raw.close()
