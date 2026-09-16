"""Building Permits Survey: the one source that makes a trend possible.

BPS ships one file per year with two merged header rows and a blank line, and
column names that cannot be parsed positionally by pandas. Three failures are
silent and each destroys the year-on-year feature rather than the row count:

  * reading only one vintage -> permits_yoy_pct is NULL for every row, and a
    tree happily trains on an all-null column;
  * dropping the leading zero on state FIPS -> '1'+'001' = '1001' instead of
    '01001', which is a valid GEOID belonging to a different state;
  * duplicate county-years surviving -> the panel's LEFT JOIN fans out and
    every ZCTA in that county is counted twice.
"""

from __future__ import annotations

import pytest

from siting_atlas.common import paths
from siting_atlas.ingest import normalise

HEADER = (
    "Survey,FIPS,FIPS,Region,Division,County,,1-unit,,,2-units,,,"
    "3-4 units,,,5+ units,,\n"
    "Date,State,County,Code,Code,Name,Bldgs,Units,Value,Bldgs,Units,Value,"
    "Bldgs,Units,Value,Bldgs,Units,Value\n"
    " \n"
)


def row(yyyymm, state, county, name, u1=0, u2=0, u34=0, u5p=0):
    return (f"{yyyymm},{state},{county},3,6,{name},"
            f"{u1},{u1},1000,{u2},{u2},2000,{u34},{u34},3000,"
            f"{u5p},{u5p},4000\n")


def write(data_root, name: str, body: str):
    folder = paths.RAW / "bps_county"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(HEADER + body, encoding="latin-1")


def test_concatenates_every_vintage_into_one_frame(data_root):
    for stem, units in (("co2112y", 100), ("co2212y", 150),
                        ("co2312y", 180)):
        write(data_root, f"{stem}.txt",
              row(f"20{stem[2:4]}12", "01", "001", "Autauga", u1=units))

    out = normalise.building_permits()
    assert sorted(out["year"].tolist()) == [2021, 2022, 2023]
    assert out["county_geoid"].nunique() == 1, (
        "one county across three vintages must stay one county")
    # A single vintage makes permits_yoy_pct null everywhere downstream; this
    # is the assertion that the concatenation actually happened.
    assert len(out) == 3


def test_deduplicates_on_county_and_year(data_root):
    """Two files carrying the same county-year must yield one row.

    The panel joins permits to every ZCTA in the county. A duplicated
    county-year multiplies those rows, and the extra rows carry the same
    values, so nothing looks wrong except the panel's row count.
    """
    write(data_root, "a_co2312y.txt",
          row(202312, "01", "001", "Autauga", u1=100))
    write(data_root, "b_co2312y_revised.txt",
          row(202312, "01", "001", "Autauga", u1=175))

    out = normalise.building_permits()
    assert len(out) == 1
    key = out[["county_geoid", "year"]]
    assert len(key) == len(key.drop_duplicates())
    # keep='last' over files sorted by name: the later vintage wins, which is
    # the revision, not the original.
    assert out["permit_units_total"].iloc[0] == 175


def test_state_and_county_fips_are_padded_before_concatenation(data_root):
    # The publisher writes unpadded FIPS in some vintages. '1'+'1' is '11',
    # zero-padded to '00011' by a naive 5-wide pad — a GEOID in DC.
    write(data_root, "co2312y.txt",
          row(202312, "1", "1", "Autauga", u1=10)
          + row(202312, "48", "85", "Denton", u1=20))
    out = normalise.building_permits().set_index("county_geoid")
    assert set(out.index) == {"01001", "48085"}
    assert all(len(g) == 5 for g in out.index)


def test_year_is_derived_from_the_yyyymm_survey_date(data_root):
    write(data_root, "co2312y.txt", row(202312, "01", "001", "A", u1=1))
    assert normalise.building_permits()["year"].tolist() == [2023]


def test_total_units_sums_every_structure_size(data_root):
    # Summing only 1-unit permits understates multifamily-heavy urban
    # counties, which are precisely the pilot metros.
    write(data_root, "co2312y.txt",
          row(202312, "01", "001", "A", u1=10, u2=4, u34=6, u5p=80))
    out = normalise.building_permits().iloc[0]
    assert out["permit_units_total"] == 100
    assert out["u1_units"] == 10
    assert out["u5p_units"] == 80


def test_a_blank_unit_count_becomes_zero_not_a_null_total(data_root):
    # A non-reporting county writes blanks. Leaving them NaN makes the whole
    # row's total NaN and silently removes the county from the trend feature.
    body = ("202312,01,001,3,6,A,,,,,,,,,,,,\n")
    write(data_root, "co2312y.txt", body)
    out = normalise.building_permits()
    assert out["permit_units_total"].iloc[0] == 0
    assert out["permit_units_total"].notna().all()


def test_footer_rows_without_a_survey_date_are_dropped(data_root):
    write(data_root, "co2312y.txt",
          row(202312, "01", "001", "A", u1=10) + ",,,,,,,,,,,,,,,,,\n")
    out = normalise.building_permits()
    assert len(out) == 1
    assert out["year"].tolist() == [2023]


def test_county_name_whitespace_is_trimmed(data_root):
    # BPS pads names to a fixed width; an untrimmed name breaks the join in
    # warehouse.build_dim_county, which matches on the string.
    write(data_root, "co2312y.txt",
          row(202312, "01", "001", "Autauga County              ", u1=1))
    assert normalise.building_permits()["county_name"].iloc[0] == (
        "Autauga County")


def test_missing_folder_raises_instead_of_returning_nothing(data_root):
    with pytest.raises(FileNotFoundError, match="ingest.acquire"):
        normalise.building_permits()


def test_building_permits_is_registered_on_the_county_grain():
    # run() logs uniqueness against this key; naming the wrong one reports a
    # reassuring "3,143 unique zcta" for a county-grain file.
    _, key = normalise.NORMALISERS["building_permits"]
    assert key == "county_geoid"
