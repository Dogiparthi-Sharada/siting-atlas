"""Credentials must not reach a log by any route.

This is a regression test for a real incident, not a hypothetical. A live
EIA_API_KEY was written into console.log, events.jsonl and errors.log at once,
because ``requests`` puts the fully expanded URL into its exception message
and the retry path logged that exception verbatim. Redacting the URL we build
ourselves was not enough.
"""

from __future__ import annotations

import pytest

from siting_atlas.common.http import _redact, _scrub

FAKE = "abc123def456ghi789jkl012mno345pq"


def test_redact_strips_known_secret_params():
    out = _redact(f"https://api.eia.gov/v2/data/?api_key={FAKE}&length=5000")
    assert FAKE not in out
    assert "api_key=<redacted>" in out
    assert "length=5000" in out, "non-secret params must survive"


def test_redact_leaves_a_bare_url_alone():
    url = "https://www2.census.gov/econ/bps/County/co2312y.txt"
    assert _redact(url) == url


def test_scrub_catches_a_key_inside_an_exception_message():
    """The exact shape of the message requests raises."""
    msg = ("HTTPError: 403 Client Error: Forbidden for url: "
           f"https://api.eia.gov/v2/petroleum/pri/gnd/data/?api_key={FAKE}"
           "&frequency=monthly")
    out = _scrub(msg)
    assert FAKE not in out
    assert "api_key=<redacted>" in out
    assert "403 Client Error" in out, "the diagnostic must remain useful"


@pytest.mark.parametrize("name", ["key", "api_key", "apikey", "token",
                                  "API_KEY", "Key"])
def test_scrub_covers_every_secret_param_name_case_insensitively(name):
    assert FAKE not in _scrub(f"https://x.test/?{name}={FAKE}")


def test_scrub_catches_a_bare_key_with_no_param_name(monkeypatch):
    """A key can appear with no `key=` around it — env values are
    scrubbed too."""
    monkeypatch.setenv("EIA_API_KEY", FAKE)
    out = _scrub(f"authentication failed for {FAKE}")
    assert FAKE not in out
    assert "<EIA_API_KEY>" in out


def test_scrub_ignores_a_suspiciously_short_env_value(monkeypatch):
    """A short value would blank out unrelated text, which is worse."""
    monkeypatch.setenv("EIA_API_KEY", "x")
    assert _scrub("the fix is in") == "the fix is in"


def test_scrub_accepts_an_exception_object():
    # The call sites pass the exception itself, not a string.
    assert FAKE not in _scrub(ValueError(f"boom api_key={FAKE}"))


def test_scrub_is_idempotent():
    once = _scrub(f"https://x.test/?api_key={FAKE}")
    assert _scrub(once) == once
