"""The OCR-to-CSV entry point, end to end on a synthetic table.

`main()` is the stage that printed a banner on the sprint's biggest artefact.
The bug class it has to be defended against is not "it crashed" — it is "it
wrote a file, printed a total, and the total was wrong". So these assert the
SHAPE of the output and the arithmetic of the counters it prints, not the
science of any single field.
"""

from __future__ import annotations

import csv

import pytest

from siting_atlas.common import log_json
from siting_atlas.ingest import mwpvl_fields as fields
from siting_atlas.ingest import mwpvl_tables as tables

from .conftest import MWPVL_CELLS


@pytest.fixture
def extraction(tmp_path, mwpvl_tsv_dir, monkeypatch):
    """Relocate the module's three hardcoded paths onto tmp_path."""
    tsv_root = tmp_path / "tsv"
    monkeypatch.setattr(tables, "TSV", tsv_root)
    monkeypatch.setattr(tables, "OUT", tmp_path / "mwpvl_facilities.csv")
    monkeypatch.setattr(tables, "REPORT", tmp_path / "mwpvl_extraction.json")
    return tsv_root


# ---------------------------------------------------------------------------
# parse_table
# ---------------------------------------------------------------------------
def test_one_table_yields_one_record_per_printed_row(mwpvl_tsv_dir):
    rows, stats = tables.parse_table(mwpvl_tsv_dir())
    assert len(rows) == len(MWPVL_CELLS)
    assert stats["rows"] == len(MWPVL_CELLS)
    assert stats["words"] > 0
    # Every column the table has must have been located. A missing entry here
    # means a whole field arrived empty on every row and nothing said so.
    assert set(stats["columns"]) == {"region", "code", "address", "sqft",
                                     "date", "description"}


def test_every_declared_output_column_is_present_on_every_record(
        mwpvl_tsv_dir):
    rows, _ = tables.parse_table(mwpvl_tsv_dir())
    for row in rows:
        missing = set(tables.COLUMNS) - set(row) - {"table", "row"}
        assert not missing, missing


def test_the_counters_match_the_records_they_count(mwpvl_tsv_dir):
    """The silent failure this guards: a stat that drifts from its rows.

    `main` prints these numbers and writes them to the artefact. If they are
    computed from anything other than the records that reach the CSV, the
    banner reports a run that did not happen.
    """
    rows, stats = tables.parse_table(mwpvl_tsv_dir())
    assert stats["with_postcode"] == sum(1 for r in rows if r["postcode"])
    assert stats["with_year"] == sum(1 for r in rows if r["open_year"])
    assert stats["with_month"] == sum(1 for r in rows if r["open_month"])
    assert stats["with_sqft"] == sum(1 for r in rows if r["sqft"])
    assert stats["with_code"] == sum(1 for r in rows if r["code"])
    # The fixture is built so none of these is trivially zero; a counter that
    # is always 0 passes the equalities above and measures nothing.
    assert stats["with_postcode"] == len(MWPVL_CELLS)
    assert 0 < stats["with_month"] < len(MWPVL_CELLS)


def test_the_fields_land_in_the_right_columns(mwpvl_tsv_dir):
    rows, _ = tables.parse_table(mwpvl_tsv_dir())
    first = rows[0]
    assert first["code"] == "DAX8"
    assert first["city"] == "Vista"
    assert first["addr_region"] == "California"
    assert first["postcode"] == "92081"
    assert first["sqft"] == 142800
    assert (first["open_year"], first["open_month"]) == (2019, 10)
    assert first["table"] == "08_us_delivery_station"


def test_the_publishers_caveat_reaches_the_record(mwpvl_tsv_dir):
    rows, _ = tables.parse_table(mwpvl_tsv_dir())
    flagged = [r for r in rows if r["not_confirmed"]]
    assert [r["code"] for r in flagged] == ["DFW9"]


def test_an_empty_directory_reports_zero_rather_than_raising(tmp_path):
    empty = tmp_path / "12_empty_table"
    empty.mkdir()
    rows, stats = tables.parse_table(empty)
    assert rows == []
    assert stats["rows"] == 0 and stats["words"] == 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def test_main_writes_a_csv_covering_every_table_it_read(extraction,
                                                        mwpvl_tsv_dir):
    mwpvl_tsv_dir("08_us_delivery_station", root=extraction)
    mwpvl_tsv_dir("08_us_delivery_station_part2", root=extraction)

    assert tables.main() == 0

    with open(tables.OUT, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 2 * len(MWPVL_CELLS)
    assert set(rows[0]) == set(tables.COLUMNS)
    assert {r["table"] for r in rows} == {"08_us_delivery_station",
                                          "08_us_delivery_station_part2"}
    # Row indices restart per table, so a (table, row) pair identifies a line
    # of OCR output. A global counter here would break traceability.
    assert [r["row"] for r in rows[:len(MWPVL_CELLS)]] \
        == [str(i) for i in range(len(MWPVL_CELLS))]


def test_main_stamps_the_artefact_with_the_run_that_wrote_it(extraction,
                                                             mwpvl_tsv_dir):
    """Audit sec.6.5. Without this the tie-break rule has nothing to read."""
    mwpvl_tsv_dir(root=extraction)
    tables.main()

    report = log_json.read_json(tables.REPORT)
    assert report["run_id"]
    assert report["written_at"]
    assert report["facilities"] == len(MWPVL_CELLS)
    assert [t["table"] for t in report["tables"]] \
        == ["08_us_delivery_station"]


def test_the_artefacts_totals_agree_with_the_csv_it_wrote(extraction,
                                                          mwpvl_tsv_dir):
    mwpvl_tsv_dir(root=extraction)
    tables.main()

    with open(tables.OUT, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    report = log_json.read_json(tables.REPORT)
    assert report["facilities"] == len(rows)
    assert report["with_year"] == sum(1 for r in rows if r["open_year"])
    assert report["not_confirmed"] == sum(1 for r in rows
                                          if r["not_confirmed"] == "True")


def test_main_refuses_to_report_success_on_an_empty_tsv_tree(extraction):
    """A banner that fires on zero output is this project's documented
    failure mode. Here it raises instead."""
    extraction.mkdir(parents=True, exist_ok=True)
    with pytest.raises(SystemExit, match="no OCR output"):
        tables.main()


def test_the_declared_columns_include_every_publisher_flag():
    for name, _ in fields.FLAGS:
        assert name in tables.COLUMNS
