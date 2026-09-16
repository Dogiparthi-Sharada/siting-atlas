"""Validating the OCR'd opening dates against the OSHA record.

The module's whole claim is that it turns "the extraction looks clean" into a
measured error rate. Three things have to hold for that claim to survive:
the date encoding must be the panel's, the charitable Q1 convention must
actually be charitable, and a missing OSHA extract must NOT read as a pass.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from siting_atlas.common import log_json, paths
from siting_atlas.ingest import mwpvl_panel as panel


def _raw(rows: list[dict]) -> pd.DataFrame:
    defaults = {"code": "DAX8", "street": "1910 E Vista Way", "city": "Vista",
                "addr_region": "California", "postcode": "92081",
                "open_year": 2019.0, "open_month": 10.0,
                "date_precision": "month", "table": "08_us_delivery_station"}
    return pd.DataFrame([{**defaults, **r} for r in rows])


# ---------------------------------------------------------------------------
# quarter_index
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("year,month,expected", [
    (2019, 1, 2019 * 4 + 0),
    (2019, 10, 2019 * 4 + 3),
    (2019, 12, 2019 * 4 + 3),
])
def test_quarter_index_is_the_panels_encoding(year, month, expected):
    assert panel.quarter_index(year, month) == expected


def test_a_year_with_no_month_lands_in_q1_which_is_the_charitable_read():
    """The edit is one-sided: it can only falsify a date for being too LATE.

    Placing an undated year in Q4 would manufacture violations and the error
    rate would measure this choice rather than the OCR.
    """
    assert panel.quarter_index(2019, None) == 2019 * 4
    assert panel.quarter_index(2019, float("nan")) == 2019 * 4


def test_a_missing_year_is_nan_and_not_an_exception():
    """pandas reads an empty cell as NaN, and NaN is truthy. `if month else`
    took the wrong branch here and int() raised on a real file."""
    assert math.isnan(panel.quarter_index(None, 10))
    assert math.isnan(panel.quarter_index(float("nan"), None))


# ---------------------------------------------------------------------------
# to_panel
# ---------------------------------------------------------------------------
def test_to_panel_renames_into_the_schema_the_edit_expects():
    out = panel.to_panel(_raw([{}]))
    assert set(out.columns) == {"facility_id", "site_address", "city",
                                "state", "zip", "open_q_index",
                                "date_precision", "table"}
    row = out.iloc[0]
    # The state arrives as a name and leaves as the two-letter code OSHA
    # files. A join on the un-mapped name silently matches nothing.
    assert row["state"] == "CA"
    assert row["facility_id"] == "DAX8"
    assert row["open_q_index"] == 2019 * 4 + 3


def test_a_row_with_no_code_still_gets_an_identifier():
    out = panel.to_panel(_raw([{"code": None}]))
    assert out["facility_id"].iloc[0].startswith("mwpvl_")


def test_an_unrecognised_region_leaves_the_state_empty_rather_than_guessing():
    out = panel.to_panel(_raw([{"addr_region": "Taxas"}]))
    assert out["state"].iloc[0] == ""


def test_row_count_is_preserved_so_an_index_still_names_a_line_of_ocr():
    out = panel.to_panel(_raw([{}, {"code": "DSM5"}, {"code": None}]))
    assert len(out) == 3


# ---------------------------------------------------------------------------
# date_plausibility
# ---------------------------------------------------------------------------
def test_the_2013_floor_applies_to_delivery_stations_only():
    """Scoping this wrongly flagged 29 legitimate facilities as errors.

    Amazon's fulfilment network began in 1997; only the last-mile delivery
    station network started in late 2013. A bound applied to the wrong
    population manufactures failures.
    """
    frame = _raw([
        {"open_year": 2010.0, "table": "01_us_fulfillment_center"},
        {"open_year": 2008.0, "table": "01_us_fulfillment_center"},
        {"open_year": 2011.0, "table": "08_us_delivery_station"},
        {"open_year": 2019.0, "table": "08_us_delivery_station"},
    ])
    got = panel.date_plausibility(frame)
    assert got["delivery_station_rows_dated"] == 2
    assert got["before_network_start"] == 1


def test_an_implausible_year_is_counted_and_named_not_repaired():
    frame = _raw([{"open_year": 2094.0, "code": "DBAD"},
                  {"open_year": 2019.0}])
    got = panel.date_plausibility(frame)
    assert got["beyond_plausible"] == 1
    assert got["implausible_codes"] == ["DBAD"]
    assert got["max_year"] == 2094


def test_undated_rows_are_excluded_from_the_denominator():
    frame = _raw([{"open_year": 2019.0}, {"open_year": None}])
    got = panel.date_plausibility(frame)
    assert got["dated"] == 1
    assert sum(got["by_year"].values()) == 1


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
@pytest.fixture
def sources(data_root, monkeypatch, tmp_path):
    """Relocate the module's two hardcoded paths and write a tiny input."""
    source = tmp_path / "mwpvl_facilities.csv"
    report = tmp_path / "mwpvl_validation.json"
    monkeypatch.setattr(panel, "SOURCE", source)
    monkeypatch.setattr(panel, "REPORT", report)
    _raw([{}, {"code": "DSM5", "street": "6910 SE Four Mile Drive",
               "city": "Ankeny", "addr_region": "Iowa", "postcode": "50021",
               "open_year": 2022.0, "open_month": 1.0}]).to_csv(source,
                                                                index=False)
    return source, report


def test_a_missing_extract_says_so_instead_of_writing_an_empty_report(
        sources):
    source, _ = sources
    source.unlink()
    with pytest.raises(SystemExit, match="not found"):
        panel.main()


def test_an_absent_osha_extract_is_not_a_pass(sources):
    """"Cannot be evaluated" and "passed" are different states. Reading one
    as the other is how an unvalidated extraction ships as a validated one."""
    assert not (paths.INTERIM / "osha_amazon.csv").exists()
    with pytest.raises(SystemExit, match="CANNOT BE EVALUATED"):
        panel.main()


def test_main_writes_a_stamped_report_when_osha_is_present(sources, capsys):
    _, report = sources
    pd.DataFrame([{"activity_nr": "1", "site_address": "1910 E VISTA WAY",
                   "site_city": "VISTA", "site_state": "CA",
                   "site_zip": "92081", "operating_by": "2020-06-01"}]
                 ).to_csv(paths.INTERIM / "osha_amazon.csv", index=False)

    assert panel.main() == 0
    got = log_json.read_json(report)
    assert got["run_id"] and got["written_at"]
    assert got["rows_with_date"] == 2
    assert got["linked_to_osha"] == 1
    # Opened 2019Q4, inspected 2020-06: consistent, so nothing is falsified.
    assert got["falsified"] == 0
    assert got["pass_rate"] == 1.0
    assert got["date_plausibility"]["dated"] == 2
    assert "MWPVL opening dates vs the OSHA record" in capsys.readouterr().out


def test_a_date_after_the_inspection_is_reported_not_dropped(sources):
    """REPORT, not EXCLUDE. Excluding failures before counting them destroys
    the measurement the module exists to make."""
    source, report = sources
    frame = pd.read_csv(source)
    frame.loc[0, "open_year"] = 2024
    frame.to_csv(source, index=False)
    pd.DataFrame([{"activity_nr": "1", "site_address": "1910 E VISTA WAY",
                   "site_city": "VISTA", "site_state": "CA",
                   "site_zip": "92081", "operating_by": "2020-06-01"}]
                 ).to_csv(paths.INTERIM / "osha_amazon.csv", index=False)

    panel.main()
    got = log_json.read_json(report)
    assert got["falsified"] == 1
    assert got["rows_with_date"] == 2      # still both rows; nothing dropped
    assert len(got["failures"]) == 1
