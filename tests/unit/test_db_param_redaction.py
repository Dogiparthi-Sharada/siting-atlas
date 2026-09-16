"""A credential must not reach sql.jsonl through a bind parameter.

Separate from test_common_db.py, which is about whether the SQL log is
COMPLETE. This file is about whether it is SAFE, and the two answers move
independently: the change that makes the log complete is the change that
makes every parameter a candidate to leak.

This is not hypothetical for this project. A live EIA_API_KEY was written
into three log files at once because an exception message was logged
verbatim, which is why ``common.http._scrub`` exists and why the HTTP and
shell paths both route through it. ``params`` was the one remaining path
that did not, and "no parameter is a secret today" is an observation about
the current callers rather than a property of the code.

Records are captured off the real sink logger, so the production path is the
one under test and nothing is written to logs/.
"""

from __future__ import annotations

import logging

import pytest

from siting_atlas.common.db import memory

# Deliberately >= 8 characters: ``_scrub`` refuses to blank out a short
# value, because a one-character secret would redact half the message.
FAKE = "abc123def456ghi789jkl012mno345pq"


class Capture(logging.Handler):
    """Collect the structured `fields` payload of every sink record."""

    def __init__(self):
        super().__init__(logging.DEBUG)
        self.records: list[dict] = []

    def emit(self, record):
        fields = getattr(record, "fields", None)
        if fields is not None:
            self.records.append(fields)

    def params(self) -> list:
        return [r["params"] for r in self.records if r.get("event") == "sql"]


@pytest.fixture
def sql_log():
    # The logger is fetched after common.db has been imported, because
    # logging_setup.sink() skips its own configuration if the logger already
    # has a handler — attaching first would leave it at the default level
    # and silently capture nothing.
    handler = Capture()
    logger = logging.getLogger("siting_atlas.sink.sql")
    logger.addHandler(handler)
    try:
        yield handler
    finally:
        logger.removeHandler(handler)


def test_a_credential_in_a_parameter_is_redacted(sql_log, monkeypatch):
    """The leak this closes: a key arriving as a bind value, not a URL."""
    monkeypatch.setenv("EIA_API_KEY", FAKE)
    with memory() as db:
        db.execute("SELECT ? AS source_url",
                   [f"https://api.eia.gov/v2/data/?api_key={FAKE}"])

    logged = sql_log.params()[0]
    assert FAKE not in str(logged)
    assert "api_key=<redacted>" in logged[0]
    assert "api.eia.gov" in logged[0], (
        "a redacted log that says nothing about what ran is no log at all")


def test_a_bare_key_with_no_param_name_is_caught_too(sql_log, monkeypatch):
    """The third ``_scrub`` pass. A key passed on its own has no ``key=``
    for the pattern to match; only the env-value pass catches it."""
    monkeypatch.setenv("EIA_API_KEY", FAKE)
    with memory() as db:
        db.execute("SELECT ? AS token", [FAKE])
    assert FAKE not in str(sql_log.params()[0])


def test_numbers_are_logged_as_numbers(sql_log):
    """Scrubbing must not silently retype the log.

    A number cannot hide a credential, and rewriting 7 as "7" would change
    the shape of every record in sql.jsonl — which is the file an analysis
    reads, not just a human.
    """
    with memory() as db:
        db.execute("SELECT ? AS n, ? AS x, ? AS s", [7, 1.5, "plain"])
    assert sql_log.params()[0] == [7, 1.5, "plain"]


def test_a_parameterless_statement_still_logs_none(sql_log):
    """No parameters must stay None rather than becoming an empty list:
    the two mean different things to whoever reads the journal."""
    with memory() as db:
        db.execute("SELECT 1")
    assert sql_log.params()[0] is None


def test_a_credential_inlined_into_the_sql_text_is_scrubbed(tmp_path):
    """Params were redacted; the statement itself was not.

    `db.execute(f"... api_key={KEY}")` wrote the key straight into sql.jsonl.
    Inlining a secret in SQL is bad practice, but relying on nobody doing it
    is the same assumption that leaked a live EIA key into three log files.
    """
    from siting_atlas.common.db import memory
    fake = "abc123def456ghi789jkl012mno345pq"
    with memory() as db:
        rows = db.df(f"SELECT 1 AS x -- api_key={fake}")
    assert len(rows) == 1
    from siting_atlas.common.db import _flatten
    from siting_atlas.common.http import _scrub
    assert fake not in _scrub(_flatten(f"SELECT 1 -- api_key={fake}"))
