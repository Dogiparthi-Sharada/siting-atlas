"""The Q1 opening-quarter convention, made visible instead of invisible.

Split out of ``test_facilities.py`` when that module crossed 300 lines.

19 of the 43 delivered facility rows (44.2%) have no ``open_quarter``, which
puts 35.47% of fitted events in Q1 against 25% expected under uniformity —
``outputs/metrics/hazard_report.json`` has measured that all along. Until
2026-09-13 the original NULL was destroyed at load, so no model could tell a
convention from a date and nothing could act on the measurement.

Q1-by-convention is the same defect class as the ACS $250,001 top code: Rahm &
Do's *missing values*, a substitute standing where a measurement is absent, and
Van den Broeck's *erroneous inlier* — plausible, in range, and invisible to
every check the project runs. Both are declared in ``common/sentinels.py``.

Every test here fails on the pre-fix code: ``open_quarter_imputed`` did not
exist.
"""

from __future__ import annotations

import pandas as pd

from siting_atlas.warehouse.facilities import enabled_flags, load_facilities

from .test_facilities import GEO, facility, panel_keys


# ---------------------------------------------------------------------------
# the Q1 convention, made visible
#
# 19 of the 43 delivered rows (44.2%) have no open_quarter, which puts 35.47%
# of fitted events in Q1 against 25% expected under uniformity —
# `outputs/metrics/hazard_report.json` has measured that all along. Until
# 2026-09-13 the original NULL was destroyed at load, so no model could tell
# a convention from a date and nothing could act on the measurement. These
# fail on the pre-fix code: `open_quarter_imputed` did not exist.
# ---------------------------------------------------------------------------
def test_load_retains_the_null_quarter_and_flags_the_default(tmp_path):
    """Van den Broeck's reversibility rule: the original value is kept."""
    f = tmp_path / "facilities.csv"
    f.write_text(
        "facility_id,operator,facility_type,city,state,zip,open_year,"
        "open_quarter,source_url,source_type\n"
        "A,Amazon,DS,Chicago,IL,60608,2020,,https://x.test,news\n"
        "B,Amazon,DS,Chicago,IL,60629,2020,3,https://x.test,permit\n",
        encoding="utf-8")

    frame = load_facilities(f).set_index("facility_id")
    assert pd.isna(frame.loc["A", "open_quarter"]), (
        "the original NULL must survive — it is the only recovery path")
    assert frame.loc["A", "open_quarter_imputed"]
    assert not frame.loc["B", "open_quarter_imputed"]
    # The operative value is unchanged: Q1 by convention, as before.
    assert frame.loc["A", "open_q_index"] == 2020 * 4
    assert frame.loc["B", "open_q_index"] == 2020 * 4 + 2


def test_the_flag_travels_with_the_date_into_the_target():
    got = enabled_flags(panel_keys(), facility(open_year=2020,
                                               open_quarter=None), GEO)
    on = got[got["enabled"]]
    assert on["open_quarter_imputed"].all()
    # A ZCTA no catchment covers is not "unknown": it has no switch-on
    # quarter at all, so the predicate is definitely false.
    off = got[got["zcta"] == "60805"]
    assert not off["open_quarter_imputed"].any()
    assert got["open_quarter_imputed"].dtype == bool


def test_an_observed_station_that_opened_first_clears_the_flag():
    """The flag belongs to the facility that SET the switch-on date.

    A ZIP switched on by a dated station in 2019 and joined by an undated one
    in 2021 has an observed switch-on date; flagging it would overstate the
    artefact and make the correction look bigger than it is.
    """
    dated = facility(facility_id="A", open_year=2019, open_quarter=1)
    undated = facility(facility_id="B", open_year=2021, open_quarter=None)
    got = enabled_flags(panel_keys(),
                        pd.concat([dated, undated], ignore_index=True), GEO)
    assert not got[got["zcta"] == "60608"]["open_quarter_imputed"].any()

    # Reverse the order and the flag has to fire.
    first_undated = facility(facility_id="B", open_year=2019,
                             open_quarter=None)
    later = facility(facility_id="A", open_year=2021, open_quarter=1)
    got = enabled_flags(
        panel_keys(), pd.concat([first_undated, later], ignore_index=True),
        GEO)
    assert got[got["zcta"] == "60608"]["open_quarter_imputed"].all()
