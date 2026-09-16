"""Tests for the facility panel to ``enabled`` target conversion.

Written before the real facilities.csv exists, deliberately: this module is
the last thing standing between a delivered file and a fitted model, so it
must be proven correct while there is time, not on the day the data lands.

Every failure mode here is silent. A wrong catchment radius, a dropped
left-censored facility, or a facility type that shouldn't set the target all
produce a plausible-looking boolean column and a model that answers the wrong
question.
"""

from __future__ import annotations

import pandas as pd
import pytest

from siting_atlas.warehouse.facilities import (
    LAST_MILE_TYPES,
    catchments,
    enabled_flags,
    load_facilities,
    resolve_coordinates,
)

# Three ZCTAs on a north-south line out of downtown Chicago. Spacing is about
# 6.9 miles per 0.1 degree of latitude, so 'near' is inside a delivery
# station's 15-mile catchment and 'far' is well outside it.
GEO = pd.DataFrame({
    "zcta": ["60608", "60629", "60805"],
    "latitude": [41.8500, 41.9500, 43.0000],
    "longitude": [-87.6800, -87.6800, -87.6800],
})


def facility(**over) -> pd.DataFrame:
    base = {"facility_id": "AMZ-DCH1", "operator": "Amazon",
            "facility_type": "DS", "city": "Chicago", "state": "IL",
            "zip": "60608", "latitude": 41.8500, "longitude": -87.6800,
            "open_year": 2020, "open_quarter": 2,
            "close_year": None, "close_quarter": None,
            "status": "open", "source_url": "https://x.test",
            "source_type": "press_release", "confidence": "high"}
    base.update(over)
    row = pd.DataFrame([base])
    row["zcta"] = row["zip"]
    row["open_q_index"] = (row["open_year"] * 4
                           + row["open_quarter"].fillna(1) - 1)
    row["close_q_index"] = (
        row["close_year"] * 4
        + row["close_quarter"].fillna(4) - 1).fillna(float("inf"))
    return row


def panel_keys(years=(2019, 2020, 2021)) -> pd.DataFrame:
    return pd.DataFrame(
        [{"zcta": z, "year": y, "quarter": q}
         for z in GEO.zcta for y in years for q in (1, 2, 3, 4)])


# ---------------------------------------------------------------------------
# which facilities set the target
# ---------------------------------------------------------------------------
def test_only_last_mile_types_are_recognised():
    """A fulfillment centre is regional; it does not put a van on a street."""
    assert {"DS", "SDC"} == LAST_MILE_TYPES


def test_a_fulfillment_centre_enables_nothing():
    """The exact mistake in the first batch of collected data: 7 FC, 0 DS.

    If FC set the target, the model would answer 'where does Amazon warehouse
    things', which has a different answer from 'where can you get a parcel
    the same day'.
    """
    got = enabled_flags(panel_keys(), facility(facility_type="FC"), GEO)
    assert not got["enabled"].any()


def test_a_delivery_station_enables_its_catchment():
    got = enabled_flags(panel_keys(), facility(), GEO)
    on = got[got["enabled"]]
    assert set(on["zcta"]) == {"60608", "60629"}, (
        "the 6.9-mile neighbour must be inside a 15-mile catchment and the "
        "79-mile one must not")


# ---------------------------------------------------------------------------
# timing
# ---------------------------------------------------------------------------
def test_the_target_switches_on_in_the_opening_quarter_not_before():
    got = enabled_flags(panel_keys(), facility(open_year=2020,
                                               open_quarter=2), GEO)
    near = got[got["zcta"] == "60608"].set_index(["year", "quarter"])
    assert not near.loc[(2020, 1), "enabled"]
    assert near.loc[(2020, 2), "enabled"]
    assert near.loc[(2020, 3), "enabled"]
    assert not near.loc[(2019, 4), "enabled"]


def test_a_facility_open_before_the_panel_starts_enables_from_day_one():
    """Left censoring. Dropping these rows would tell the model the ZIP was
    waiting to be switched on when it never was."""
    got = enabled_flags(panel_keys(), facility(open_year=2014,
                                               open_quarter=3), GEO)
    near = got[got["zcta"] == "60608"]
    assert near["enabled"].all()


def test_a_closed_facility_switches_its_catchment_back_off():
    got = enabled_flags(
        panel_keys(),
        facility(open_year=2019, open_quarter=1, close_year=2020,
                 close_quarter=2, status="closed"), GEO)
    near = got[got["zcta"] == "60608"].set_index(["year", "quarter"])
    assert near.loc[(2019, 3), "enabled"]
    assert near.loc[(2020, 2), "enabled"], "closes AT the end of its quarter"
    assert not near.loc[(2020, 3), "enabled"]


def test_two_overlapping_stations_keep_a_zip_on_when_one_closes():
    """A ZIP served by two stations must not go dark because one shut."""
    a = facility(facility_id="A", open_year=2019, open_quarter=1,
                 close_year=2020, close_quarter=1)
    b = facility(facility_id="B", open_year=2019, open_quarter=1)
    got = enabled_flags(panel_keys(), pd.concat([a, b], ignore_index=True),
                        GEO)
    near = got[got["zcta"] == "60608"].set_index(["year", "quarter"])
    assert near.loc[(2021, 4), "enabled"]


def test_a_missing_quarter_defaults_to_q1_rather_than_dropping_the_row():
    """Blank quarters are expected and honest; losing the event is not."""
    got = enabled_flags(panel_keys(), facility(open_year=2020,
                                               open_quarter=None), GEO)
    near = got[got["zcta"] == "60608"].set_index(["year", "quarter"])
    assert near.loc[(2020, 1), "enabled"]
    assert not near.loc[(2019, 4), "enabled"]


# ---------------------------------------------------------------------------
# robustness
# ---------------------------------------------------------------------------
def test_coordinates_fall_back_to_the_zcta_centroid():
    """Most press releases name a street, not a latitude."""
    filled = resolve_coordinates(
        facility(latitude=None, longitude=None), GEO)
    assert filled["latitude"].iloc[0] == pytest.approx(41.8500)


def test_a_facility_with_no_coordinate_and_no_centroid_enables_nothing():
    """It must be dropped from the catchment, not crash and not match all."""
    orphan = facility(zip="99999", latitude=None, longitude=None)
    orphan["zcta"] = "99999"
    filled = resolve_coordinates(orphan, GEO)
    assert catchments(filled, GEO).empty


def test_an_empty_facility_file_raises_rather_than_returning_nothing(tmp_path):
    """A header-only file is exactly what arrived first; it must not pass
    silently as 'no facilities were open anywhere'."""
    f = tmp_path / "facilities.csv"
    f.write_text("facility_id,operator,facility_type,city,state,zip,"
                 "open_year,source_url,source_type\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no data rows"):
        load_facilities(f)


def test_leading_zeros_survive_the_read(tmp_path):
    """01890 must not become 1890. The single most common handoff failure."""
    f = tmp_path / "facilities.csv"
    f.write_text(
        "facility_id,operator,facility_type,city,state,zip,latitude,"
        "longitude,open_year,open_quarter,source_url,source_type\n"
        "A,Amazon,DS,Winchester,MA,01890,42.45,-71.14,2021,2,"
        "https://x.test,news\n", encoding="utf-8")
    assert load_facilities(f)["zcta"].iloc[0] == "01890"


def test_every_panel_key_gets_a_row_even_when_never_enabled():
    """A left join that loses rows would shrink the panel silently."""
    keys = panel_keys()
    got = enabled_flags(keys, facility(), GEO)
    assert len(got) == len(keys)
    assert got["enabled"].dtype == bool
    assert not got["enabled"].isna().any()


# ---------------------------------------------------------------------------
# the switchover
# ---------------------------------------------------------------------------
def test_attach_populates_the_target_with_no_code_change(tmp_path):
    """The day facilities.csv lands, this is the whole switchover.

    `attach` is what `warehouse.panel` calls unconditionally. Absent file ->
    NULL target and a warning; present file -> populated target. No flag, no
    branch anywhere else in the pipeline.
    """
    from siting_atlas.common.db import memory
    from siting_atlas.warehouse.facilities import attach

    csv = tmp_path / "facilities.csv"
    csv.write_text(
        "facility_id,operator,facility_type,city,state,zip,latitude,"
        "longitude,open_year,open_quarter,status,source_url,source_type\n"
        "AMZ-DCH1,Amazon,DS,Chicago,IL,60608,41.85,-87.68,2020,2,open,"
        "https://x.test,press_release\n", encoding="utf-8")

    with memory() as db:
        db.register("k", panel_keys())
        db.register("g", GEO)
        db.execute("CREATE TEMP TABLE panel AS SELECT *, "
                   "CAST(NULL AS BOOLEAN) AS enabled, "
                   "CAST(NULL AS BOOLEAN) AS open_quarter_imputed FROM k")
        db.execute("CREATE TEMP TABLE dim_zcta AS SELECT * FROM g")

        assert db.scalar("SELECT COUNT(*) FROM panel WHERE enabled") == 0
        n = attach(db, csv)

        assert n > 0, "the target did not populate"
        assert db.scalar("SELECT COUNT(*) FROM panel WHERE enabled") == n
        # Grain must survive the join — a fan-out here would silently
        # duplicate every enabled ZCTA-quarter.
        assert db.scalar("SELECT COUNT(*) FROM panel") == len(panel_keys())


def test_attach_is_a_warning_not_a_failure_when_the_file_is_absent(tmp_path):
    """L0-L3 stay useful while the target is still being collected."""
    from siting_atlas.common.db import memory
    from siting_atlas.warehouse.facilities import attach

    with memory() as db:
        db.register("k", panel_keys())
        db.execute("CREATE TEMP TABLE panel AS SELECT *, "
                   "CAST(NULL AS BOOLEAN) AS enabled, "
                   "CAST(NULL AS BOOLEAN) AS open_quarter_imputed FROM k")
        assert attach(db, tmp_path / "nope.csv") == 0


# ---------------------------------------------------------------------------
# closure validation
#
# Added when the delivered panel gained its first closed site (the Chicago
# 2801 S Western delivery station, DCH1, closed 2021Q1). Until then no row
# had ever exercised the close_year path, so none of these failures could
# have been noticed by running the pipeline.
# ---------------------------------------------------------------------------
def _row(**over):
    base = {"facility_id": "DS-001", "operator": "Amazon",
            "facility_type": "DS", "city": "CHICAGO", "state": "IL",
            "zip": "60608", "open_year": "2015", "open_quarter": "",
            "close_year": "", "close_quarter": "", "status": "open",
            "source_url": "x", "source_type": "permit"}
    return {**base, **over}


def test_closed_without_a_date_is_an_error():
    """Otherwise the catchment stays enabled forever and the closure is
    silently lost."""
    from siting_atlas.ingest.facility_check import _closure_errors
    errors = _closure_errors([_row(status="closed")])
    assert errors and "close_year" in errors[0]


def test_closed_with_a_date_is_accepted():
    from siting_atlas.ingest.facility_check import _closure_errors
    assert _closure_errors([_row(status="closed", close_year="2021",
                                 close_quarter="1")]) == []


def test_closing_before_opening_is_an_error():
    """An empty service window makes the facility enable nothing at all."""
    from siting_atlas.ingest.facility_check import _closure_errors
    errors = _closure_errors([_row(open_year="2021", close_year="2019",
                                   status="closed", close_quarter="4")])
    assert errors and "close before they open" in errors[0]


def test_close_quarter_outside_one_to_four_is_an_error():
    from siting_atlas.ingest.facility_check import _closure_errors
    errors = _closure_errors([_row(close_year="2021", close_quarter="0")])
    assert errors and "close_quarter" in errors[0]
