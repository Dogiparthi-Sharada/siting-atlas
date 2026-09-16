"""Tests for the build gate that stops a quality flag being dropped.

The gate exists because three of the audit's findings are one bug: something
upstream computes a boolean recording *how a value came to be*, and the value
survives to the panel while the boolean does not. Nothing failed, because
nothing was checking.

``test_no_computed_flag_is_lost_on_the_real_artefacts`` is the test the gate
was written for. It failed on the code as it stood, naming three flags:

    median_home_value_topcoded          computed in acs5_zcta_2023
    median_household_income_topcoded    computed in acs5_zcta_2023
    wage_suppressed                     computed in bls_wages
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from siting_atlas.common import paths
from siting_atlas.common.db import memory
from siting_atlas.warehouse import flag_gate


def _interim(tmp_path, **frames):
    """Write one parquet per keyword argument into a fake interim dir."""
    for name, frame in frames.items():
        frame.to_parquet(tmp_path / f"{name}.parquet", index=False)
    return tmp_path


def _panel(db, **columns):
    db.register("src", pd.DataFrame(columns))
    db.execute("CREATE OR REPLACE TEMP TABLE panel AS SELECT * FROM src")


# ---------------------------------------------------------------------------
# the naming convention that is the contract
# ---------------------------------------------------------------------------
def test_every_flag_suffix_in_use_is_recognised():
    """Four conventions were in the repo before this gate; all must count."""
    for column in ("rent_observed", "income_imputed", "wage_suppressed",
                   "median_home_value_topcoded",
                   "median_household_income_bottomcoded"):
        assert flag_gate.is_flag(column), column


def test_an_ordinary_column_is_not_a_flag():
    for column in ("median_home_value", "population", "enabled", "zcta"):
        assert not flag_gate.is_flag(column)


# ---------------------------------------------------------------------------
# detection
# ---------------------------------------------------------------------------
def test_computed_flags_finds_the_flag_and_names_its_artefact(tmp_path):
    _interim(tmp_path,
             acs=pd.DataFrame({"zcta": ["00601"], "income": [1.0],
                               "income_topcoded": [True]}),
             cbp=pd.DataFrame({"zcta": ["00601"], "employment": [3.0]}))
    assert flag_gate.computed_flags(tmp_path) == {"income_topcoded": "acs"}


def test_a_corrupt_interim_file_warns_rather_than_taking_the_build_down(
        tmp_path):
    """A half-written parquet must not be indistinguishable from 'no flags'
    — but it must also not stop a build that has nothing to do with it."""
    (tmp_path / "broken.parquet").write_bytes(b"not a parquet")
    assert flag_gate.computed_flags(tmp_path) == {}


# ---------------------------------------------------------------------------
# the gate itself
# ---------------------------------------------------------------------------
def test_the_gate_fails_when_a_computed_flag_is_dropped(tmp_path):
    """The exact shape of the census_api top-code bug, in miniature."""
    _interim(tmp_path, acs=pd.DataFrame({
        "zcta": ["00601"], "median_household_income": [250001.0],
        "median_household_income_topcoded": [True]}))

    with memory() as db:
        _panel(db, zcta=["00601"], median_household_income=[250001.0])
        with pytest.raises(ValueError, match="never reach") as exc:
            flag_gate.assert_flags_carried(
                db, interim=tmp_path, declared={})

    assert "median_household_income_topcoded" in str(exc.value)
    assert "acs" in str(exc.value), "the error must say where to go and look"


def test_the_gate_passes_once_the_flag_is_carried(tmp_path):
    _interim(tmp_path, acs=pd.DataFrame({
        "zcta": ["00601"], "median_household_income": [250001.0],
        "median_household_income_topcoded": [True]}))

    with memory() as db:
        _panel(db, zcta=["00601"], median_household_income=[250001.0],
               median_household_income_topcoded=[True])
        report = flag_gate.assert_flags_carried(
            db, interim=tmp_path, declared={})

    assert report["dropped"] == {}
    assert report["carried"] == ["median_household_income_topcoded"]


def test_the_gate_covers_flags_computed_inside_the_warehouse(tmp_path):
    """``open_quarter_imputed`` comes from a CSV, not from an L1 parquet.

    Without ``extra`` the gate would have no way to see the facility panel's
    flags at all, and fix 2 would be unguarded by the gate written for it.
    """
    _interim(tmp_path)
    with memory() as db:
        _panel(db, zcta=["00601"], enabled=[True])
        with pytest.raises(ValueError, match="open_quarter_imputed"):
            flag_gate.assert_flags_carried(
                db, interim=tmp_path, declared={},
                extra={"open_quarter_imputed": "facilities.csv"})


def test_a_non_flag_column_upstream_is_not_demanded_of_the_panel(tmp_path):
    """The gate must not turn into 'the panel carries every interim column'.

    ``ejscreen_tract`` has 11 columns and the panel wants 5 of them; a gate
    that insisted on all of them would be turned off within a week.
    """
    _interim(tmp_path, ej=pd.DataFrame({"tract_geoid": ["09110400101"],
                                        "pm25": [7.1], "ozone": [40.0]}))
    with memory() as db:
        _panel(db, zcta=["00601"], pm25=[7.1])
        assert flag_gate.assert_flags_carried(
            db, interim=tmp_path, declared={})["dropped"] == {}


def test_a_declared_sentinel_that_never_ran_is_caught(tmp_path):
    """The registry is checked as well as the artefacts, and it fails
    differently: a flag declared in common/sentinels.py and absent from the
    interim parquet means the DETECTOR never ran, not that the warehouse
    dropped it. Both end as "the panel cannot see it"."""
    _interim(tmp_path)
    with memory() as db:
        _panel(db, zcta=["00601"])
        with pytest.raises(ValueError, match="sentinel registry"):
            flag_gate.assert_flags_carried(
                db, interim=tmp_path,
                declared={"median_home_value_topcoded": "acs5_zcta"})


def test_the_real_registry_is_what_the_gate_defends_by_default():
    """No caller has to remember to pass the registry in."""
    from siting_atlas.common.sentinels import all_flags

    report = flag_gate.check([], interim=tmp_path_none())
    assert set(all_flags()) <= set(report["computed"])


def tmp_path_none():
    """An empty directory, so only the registry contributes."""
    import tempfile
    return Path(tempfile.mkdtemp())


# ---------------------------------------------------------------------------
# the real artefacts — this is the one the gate was written for
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not paths.PANEL.exists(),
                    reason="needs a built panel; run make panel")
def test_no_computed_flag_is_lost_on_the_real_artefacts():
    """Every flag any real L1 artefact computes is in the real panel.

    Failed before fixes 1 and 2 with three dropped flags; see this module's
    docstring for the exact message.
    """
    from siting_atlas.warehouse.facilities import WAREHOUSE_FLAGS

    columns = pd.read_parquet(paths.PANEL).columns
    report = flag_gate.check(columns, extra=WAREHOUSE_FLAGS)
    assert report["dropped"] == {}, (
        "a quality flag computed upstream never reaches panel.parquet")
    assert report["computed"], "no flags found at all — the scan is broken"
