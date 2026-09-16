"""Filesystem layout and configuration loading.

paths.py is the reason the pipeline can be relocated to CI with one variable;
config.py is the reason a credential never reaches disk. Both fail quietly
when they fail: a wrong root writes artefacts somewhere nobody looks, and a
leaked key is only noticed by whoever finds it.
"""

from __future__ import annotations

import importlib
import os

import pytest

from siting_atlas.common import config, paths


# ---------------------------------------------------------------------------
# paths
# ---------------------------------------------------------------------------
def test_root_is_overridable_by_one_environment_variable(tmp_path,
                                                         monkeypatch):
    monkeypatch.setenv("SITING_ATLAS_ROOT", str(tmp_path))
    relocated = importlib.reload(paths)
    try:
        expected = tmp_path / "data" / "processed" / "panel.parquet"
        assert tmp_path == relocated.ROOT  # noqa: SIM300
        assert expected == relocated.PANEL  # noqa: SIM300
        assert relocated.MANIFEST.parent == relocated.RAW
    finally:
        monkeypatch.delenv("SITING_ATLAS_ROOT", raising=False)
        importlib.reload(paths)


def test_default_root_is_the_repo_not_the_working_directory():
    # Derived from __file__, so running pytest from any cwd still resolves.
    assert (paths.ROOT / "src" / "siting_atlas").is_dir()
    assert paths.ROOT.is_absolute()


def test_layers_nest_the_way_the_handbook_says():
    assert paths.RAW.parent == paths.DATA
    assert paths.INTERIM.parent == paths.DATA
    assert paths.WAREHOUSE.parent == paths.PROCESSED
    assert paths.PANEL.parent == paths.PROCESSED
    assert paths.METRICS.parent == paths.OUTPUTS


def test_ensure_dirs_creates_every_writable_directory_and_is_idempotent(
        tmp_path, monkeypatch):
    made = [tmp_path / n for n in ("raw", "interim", "outputs")]
    monkeypatch.setattr(paths, "_WRITABLE", tuple(made))
    paths.ensure_dirs()
    paths.ensure_dirs()           # must not raise on the second call
    assert all(d.is_dir() for d in made)


def test_rel_shortens_a_path_inside_the_repo():
    assert paths.rel(paths.PANEL) == os.path.join(
        "data", "processed", "panel.parquet")


def test_rel_falls_back_to_the_absolute_path_outside_the_repo():
    # A log line must never be *wrong*; an unrelativisable path is printed in
    # full rather than mangled into a misleading '../../..' chain.
    assert paths.rel("/etc/hostname") == "/etc/hostname"


def test_rel_accepts_a_string_as_well_as_a_path():
    assert paths.rel(str(paths.INTERIM)) == "data/interim"


def test_rel_works_when_the_root_is_given_relatively(tmp_path, monkeypatch):
    # Was an xfail: ROOT was taken verbatim from SITING_ATLAS_ROOT while
    # rel() compares against path.resolve(), so a relative or symlinked root
    # never matched and every log line printed an absolute path. ROOT is now
    # .resolve()'d at construction, as _DEFAULT_ROOT always was.
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    monkeypatch.setenv("SITING_ATLAS_ROOT", ".")
    relocated = importlib.reload(paths)
    try:
        assert relocated.rel(tmp_path / "data" / "x.parquet") == (
            "data/x.parquet")
    finally:
        monkeypatch.delenv("SITING_ATLAS_ROOT", raising=False)
        importlib.reload(paths)


# ---------------------------------------------------------------------------
# config: .env loading
# ---------------------------------------------------------------------------
@pytest.fixture
def fresh_env(monkeypatch):
    """load_dotenv() latches a module global; reset it per test."""
    monkeypatch.setattr(config, "_ENV_LOADED", False)
    return monkeypatch


def test_dotenv_loads_keys_and_strips_quotes(tmp_path, fresh_env):
    env = tmp_path / ".env"
    env.write_text('CENSUS_API_KEY="abc123"\nEIA_API_KEY=\'def456\'\n')
    fresh_env.delenv("CENSUS_API_KEY", raising=False)
    fresh_env.delenv("EIA_API_KEY", raising=False)

    assert config.load_dotenv(env) == 2
    assert os.environ["CENSUS_API_KEY"] == "abc123"
    assert os.environ["EIA_API_KEY"] == "def456"


def test_an_existing_environment_variable_always_wins(tmp_path, fresh_env):
    # CI injects the real key; a stale .env left in a checkout must not
    # silently override it and send every request with the wrong credential.
    env = tmp_path / ".env"
    env.write_text("CENSUS_API_KEY=from_file\n")
    fresh_env.setenv("CENSUS_API_KEY", "from_ci")
    assert config.load_dotenv(env) == 0
    assert os.environ["CENSUS_API_KEY"] == "from_ci"


def test_comments_blanks_and_malformed_lines_are_skipped(tmp_path, fresh_env):
    env = tmp_path / ".env"
    env.write_text("# a comment\n\nNOT_AN_ASSIGNMENT\nSA_T_A=1\n")
    fresh_env.delenv("SA_T_A", raising=False)
    assert config.load_dotenv(env) == 1


def test_a_value_containing_an_equals_sign_is_kept_whole(tmp_path, fresh_env):
    # Base64 secrets end in '='. partition() must split on the FIRST '=' only.
    env = tmp_path / ".env"
    env.write_text("SA_T_B=abc=def==\n")
    fresh_env.delenv("SA_T_B", raising=False)
    config.load_dotenv(env)
    assert os.environ["SA_T_B"] == "abc=def=="


def test_a_missing_dotenv_is_not_an_error_and_does_not_latch(tmp_path,
                                                             fresh_env):
    # Returning early without setting _ENV_LOADED matters: a later call, once
    # the file exists, must still load it.
    assert config.load_dotenv(tmp_path / "nope.env") == 0
    assert config._ENV_LOADED is False


# ---------------------------------------------------------------------------
# config: the provenance snapshot
# ---------------------------------------------------------------------------
def test_census_key_sees_a_key_exported_after_the_first_call(monkeypatch):
    """`census_key` used to be lru_cached, so the FIRST call's answer stuck.

    Export a key after anything had already asked once and it was invisible
    for the rest of the process — which is exactly the order a notebook or a
    test session runs in.
    """
    monkeypatch.delenv("CENSUS_API_KEY", raising=False)
    monkeypatch.setattr(config, "_ENV_LOADED", True)
    assert config.census_key() is None
    monkeypatch.setenv("CENSUS_API_KEY", "exported-late-1234")
    assert config.census_key() == "exported-late-1234"


def test_describe_never_contains_the_key_itself(monkeypatch):
    """describe() is serialised into outputs/metrics and committed.

    Reporting presence rather than value is the whole point; a refactor that
    put the key in for debugging would ship it to the repository.
    """
    monkeypatch.setenv("CENSUS_API_KEY", "supersecretvalue123")
    snapshot = config.describe()
    assert "supersecretvalue123" not in repr(snapshot)
    assert snapshot["census_key_present"] is True


def test_require_census_key_names_the_fix_in_the_error(monkeypatch):
    monkeypatch.delenv("CENSUS_API_KEY", raising=False)
    monkeypatch.setattr(config, "_ENV_LOADED", True)   # block the .env read
    with pytest.raises(RuntimeError, match="key_signup"):
        config.require_census_key()


def test_pinned_vintages_are_stated_and_reported():
    # A silent vintage bump corrupts a panel without raising, so the value is
    # asserted here as well as declared.
    assert (config.ACS_YEAR, config.CBP_YEAR) == (2023, 2022)
    assert config.PANEL_START_YEAR < config.PANEL_END_YEAR
    snapshot = config.describe()
    assert snapshot["acs_year"] == config.ACS_YEAR
    assert snapshot["panel_years"] == [config.PANEL_START_YEAR,
                                       config.PANEL_END_YEAR]


def test_heldout_metros_are_a_subset_of_the_pilot():
    # A typo here removes a metro from the fit sample AND fails to add it to
    # the transfer test, shrinking the study in silence.
    assert set(config.HELDOUT_METROS) <= set(config.PILOT_METROS)
    assert len(config.PILOT_METROS) == len(set(config.PILOT_METROS))


def test_backtest_window_does_not_leak_the_future_into_training():
    assert all(y > config.BACKTEST_TRAIN_THROUGH
               for y in config.BACKTEST_PREDICT)


def test_every_acs_variable_maps_to_a_distinct_column_name():
    # Two variables mapped to one name silently drops one ACS measure.
    names = list(config.ACS_VARIABLES.values())
    assert len(names) == len(set(names))
    assert set(config.ACS_MOE_FOR) <= set(config.ACS_VARIABLES)
