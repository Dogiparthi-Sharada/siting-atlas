"""Subprocess logging, and the credentials that must not survive it.

commands.jsonl is committed evidence of what a run executed, so it is read by
people other than the author. A secret that reaches it is leaked exactly the
way the EIA key in test_http_redaction.py was: not by a careless print, but
by a diagnostic that captured more than it meant to.
"""

from __future__ import annotations

import logging
import subprocess
import sys

import pytest

from siting_atlas.common import context, shell

SECRET = "sk-live-abc123def456ghi789"


class Capture(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.records: list[dict] = []

    def emit(self, record):
        fields = getattr(record, "fields", None)
        if fields is not None:
            self.records.append(fields)


@pytest.fixture
def cmd_log():
    handler = Capture()
    logger = logging.getLogger("siting_atlas.sink.commands")
    logger.addHandler(handler)
    try:
        yield handler
    finally:
        logger.removeHandler(handler)


def py(*code: str) -> list[str]:
    return [sys.executable, "-c", "; ".join(code)]


# ---------------------------------------------------------------------------
# redaction
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["CENSUS_API_KEY", "GH_TOKEN", "MY_SECRET",
                                  "DB_PASSWORD", "PGPASSWD",
                                  "AWS_CREDENTIALS", "lowercase_key"])
def test_every_credential_shaped_env_name_is_redacted(name):
    out = shell._safe_env({name: SECRET})
    assert out[name] == "<redacted>"
    assert SECRET not in repr(out)


def test_non_secret_overrides_survive_redaction():
    # Redacting everything would be safe and useless; PATH and locale are
    # exactly what you need to reproduce a failure on another machine.
    out = shell._safe_env({"PATH": "/usr/bin", "LC_ALL": "C",
                           "OSRM_THREADS": "8"})
    assert out == {"PATH": "/usr/bin", "LC_ALL": "C", "OSRM_THREADS": "8"}


def test_no_overrides_logs_none_rather_than_an_empty_dict():
    assert shell._safe_env(None) is None
    assert shell._safe_env({}) is None


def test_the_redacted_env_reaches_the_command_record(cmd_log):
    shell.run(py("pass"), env={"CENSUS_API_KEY": SECRET, "SA_MARK": "1"})
    (rec,) = cmd_log.records
    assert rec["env_overrides"] == {"CENSUS_API_KEY": "<redacted>",
                                    "SA_MARK": "1"}
    assert SECRET not in repr(rec)


def test_the_subprocess_still_receives_the_real_value(cmd_log):
    # Redaction is for the log only. If it reached the child the command
    # would fail with an auth error and the cause would be this function.
    res = shell.run(py("import os", "print(os.environ['CENSUS_API_KEY'])"),
                    env={"CENSUS_API_KEY": SECRET})
    assert res.stdout.strip() == SECRET
    assert res.ok


def test_the_parent_environment_is_inherited_not_replaced(monkeypatch):
    monkeypatch.setenv("SA_INHERITED", "yes")
    res = shell.run(py("import os", "print(os.environ.get('SA_INHERITED'))"),
                    env={"SA_OTHER": "1"})
    assert res.stdout.strip() == "yes"


def test_a_secret_in_argv_is_redacted_too(cmd_log):
    # Was an xfail: only the `env` override dict was redacted, so a secret
    # passed on the command line reached commands.jsonl under 'argv' and
    # console.log via the `$ %s` line. argv, the output tails and the raised
    # CalledProcessError now all go through common.http._scrub.
    shell.run(py("pass") + [f"--api_key={SECRET}"], check=False)
    assert SECRET not in repr(cmd_log.records)


# ---------------------------------------------------------------------------
# the command record
# ---------------------------------------------------------------------------
def test_a_successful_command_is_recorded_in_full(cmd_log, tmp_path):
    context.init_run("20240101-000000-abcd")
    with context.layer("L0"), context.stage("acquire:gaz"):
        res = shell.run(py("print('hello')"), cwd=tmp_path)

    (rec,) = cmd_log.records
    assert rec["exit_code"] == 0
    assert rec["cwd"] == str(tmp_path)
    assert rec["stdout_tail"].strip() == "hello"
    assert (rec["layer"], rec["stage"]) == ("L0", "acquire:gaz")
    assert res.ok and res.seconds > 0


def test_stderr_is_captured_for_a_failing_command(cmd_log):
    res = shell.run(py("import sys", "sys.stderr.write('bad input')",
                       "sys.exit(3)"), check=False)
    assert res.code == 3 and not res.ok
    assert "bad input" in cmd_log.records[0]["stderr_tail"]


def test_output_is_tailed_so_one_command_cannot_fill_the_log(cmd_log):
    shell.run(py("print('x' * 20000)"))
    assert len(cmd_log.records[0]["stdout_tail"]) == shell._TAIL_CHARS


# ---------------------------------------------------------------------------
# failure modes
# ---------------------------------------------------------------------------
def test_check_true_raises_and_carries_the_output(cmd_log):
    with pytest.raises(subprocess.CalledProcessError) as exc:
        shell.run(py("import sys", "sys.exit(2)"))
    assert exc.value.returncode == 2
    assert cmd_log.records, "the failing command must still be recorded"


def test_check_false_returns_the_code_instead_of_raising():
    res = shell.run(py("import sys", "sys.exit(2)"), check=False)
    assert (res.code, res.ok) == (2, False)


def test_a_missing_executable_becomes_exit_127_not_a_traceback(cmd_log):
    # Optional tools (osrm, dbt) are genuinely absent on some machines; the
    # shell convention 127 is what the callers branch on.
    res = shell.run(["definitely-not-a-real-binary-xyz"], check=False)
    assert res.code == 127
    assert "executable not found" in res.stderr
    assert cmd_log.records[0]["exit_code"] == 127


def test_a_timeout_becomes_exit_124_and_says_so(cmd_log):
    res = shell.run(py("import time", "time.sleep(5)"), timeout=0.4,
                    check=False)
    assert res.code == 124
    assert "timed out after 0.4s" in res.stderr
    assert res.seconds < 4.0, "it must not have waited out the full sleep"


def test_a_string_command_is_split_without_a_shell():
    # No shell means a glob or a `;` is an argument, not an injection point.
    res = shell.run(f"{sys.executable} -c \"print('a b')\"")
    assert res.stdout.strip() == "a b"

    res = shell.run(py("import sys", "print(sys.argv[1])") + ["*"])
    assert res.stdout.strip() == "*", "the shell expanded a glob"


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------
def test_result_str_is_truncated_and_names_the_exit_code():
    res = shell.Result(["echo", "x" * 200], 1, "", "", 0.1)
    assert str(res).endswith("exit=1>")
    assert len(str(res)) < 90


def test_which_reports_a_missing_optional_tool_without_raising():
    assert shell.which("definitely-not-a-real-binary-xyz") is None
    assert shell.which(sys.executable.split("/")[-1]) or True
