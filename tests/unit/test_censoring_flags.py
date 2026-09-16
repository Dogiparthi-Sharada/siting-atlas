"""ACS interval-censoring codes: detected, flagged, and carried to the panel.

The Census publishes a median as the highest or lowest code in its own
tabulation when the true median falls outside the published range. Read as a
point estimate, $250,001 of household income says "this place earns a quarter
of a million dollars"; read correctly it says "at least that". Both tails were
affected and only the top was ever looked for.

These fail on the pre-fix code in two different ways:

  * ``flag_censoring`` emitted only ``*_topcoded``, so every bottom-code test
    here raised KeyError;
  * the panel carried none of the four, so the panel tests found no column.
"""

from __future__ import annotations

import pandas as pd
import pytest

from siting_atlas.common import paths
from siting_atlas.common.sentinels import BOTTOM, REGISTRY, TOP
from siting_atlas.ingest.census_api import flag_censoring

#: The counts in data/interim/acs5_zcta_2023.parquet, measured 2026-09-13.
#: Pinned as numbers rather than as ">0" because a flag that silently stops
#: firing is exactly the failure this whole exercise is about.
EXPECTED = {
    "median_home_value_topcoded": 83,
    "median_home_value_bottomcoded": 20,
    "median_household_income_topcoded": 86,
    "median_household_income_bottomcoded": 23,
}


def test_both_tails_are_declared_for_both_columns():
    """A column with only one tail declared is how the bottom codes were
    missed for a year. The registry is the place that makes the omission
    visible, so it is asserted here rather than assumed."""
    acs = REGISTRY["acs5_zcta"]
    assert {s.field for s in acs} == {"median_home_value",
                                      "median_household_income"}
    for field in {s.field for s in acs}:
        kinds = {s.kind for s in acs if s.field == field}
        assert kinds == {TOP, BOTTOM}, field
    for field in {s.field for s in acs}:
        top = next(s for s in acs if s.field == field and s.kind == TOP)
        bottom = next(s for s in acs if s.field == field and s.kind == BOTTOM)
        assert bottom.code < top.code
    # Every declared sentinel has to say WHY, or the registry is a lookup
    # table and not documentation.
    assert all(s.why for s in acs)


def test_a_value_on_the_code_is_flagged_and_left_alone():
    """Screening, not editing: the value must survive untouched."""
    frame = flag_censoring(pd.DataFrame({
        "median_household_income": [250_001.0, 2_499.0, 70_000.0, None],
        "median_home_value": [2_000_001.0, 9_999.0, 210_000.0, None]}))

    assert frame["median_household_income_topcoded"].tolist() == [
        True, False, False, False]
    assert frame["median_household_income_bottomcoded"].tolist() == [
        False, True, False, False]
    assert frame["median_home_value_topcoded"].tolist() == [
        True, False, False, False]
    assert frame["median_home_value_bottomcoded"].tolist() == [
        False, True, False, False]
    # The original value is the recovery path, so it must not have moved.
    assert frame["median_household_income"].iloc[0] == 250_001.0


def test_a_missing_value_is_not_a_censored_one():
    """NULL is 'no estimate', not 'an estimate at the bound'.

    ``.le(2499)`` on a NaN is False in pandas, but `.fillna(False)` is what
    makes the column bool rather than object, and an object column of
    True/False/NaN is the shape that reads as truthy everywhere downstream.
    """
    frame = flag_censoring(pd.DataFrame({
        "median_household_income": [None, None]}))
    assert frame["median_household_income_bottomcoded"].dtype == bool
    assert not frame["median_household_income_bottomcoded"].any()


def test_a_frame_without_the_column_is_left_alone():
    """acs1_metro has no median_home_value and must not gain a flag."""
    frame = flag_censoring(pd.DataFrame({"population": [1.0]}))
    assert list(frame.columns) == ["population"]


# ---------------------------------------------------------------------------
# the real artefacts
# ---------------------------------------------------------------------------
@pytest.mark.skipif(
    not (paths.INTERIM / "acs5_zcta_2023.parquet").exists(),
    reason="needs the ACS interim artefact")
def test_the_real_acs_release_carries_all_four_flags():
    frame = pd.read_parquet(paths.INTERIM / "acs5_zcta_2023.parquet")
    for column, n in EXPECTED.items():
        assert int(frame[column].sum()) == n, column


@pytest.mark.skipif(not paths.PANEL.exists(),
                    reason="needs a built panel; run make panel")
def test_the_flags_reach_the_panel_on_the_right_zctas():
    """The defect was here: computed in L0, present in L1, gone by L3."""
    panel = pd.read_parquet(paths.PANEL)
    zctas = panel.drop_duplicates("zcta")
    for column, n in EXPECTED.items():
        assert column in panel.columns, f"{column} lost before the panel"
        assert int(zctas[column].sum()) == n, column

    # The flag must identify the same rows the value does, or it is decorative.
    coded = zctas[zctas["median_household_income_topcoded"]]
    assert (coded["median_household_income"] == 250_001).all()
    floored = zctas[zctas["median_household_income_bottomcoded"]]
    assert (floored["median_household_income"] == 2_499).all()
