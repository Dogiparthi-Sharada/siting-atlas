"""L1's one non-negotiable rule: geographic codes stay zero-padded strings.

'01890' read as an integer becomes 1890, and 1890 joins to nothing. No
exception is raised, no row count looks odd in isolation — New England and
Puerto Rico simply vanish from the panel. Every normaliser is therefore
tested against a fixture that contains a leading-zero code, including the
already-damaged form a publisher sometimes ships.
"""

from __future__ import annotations

import pandas as pd
import pytest

from siting_atlas.common import paths
from siting_atlas.ingest import normalise

LEADING_ZERO = ("01890", "02135", "00501")


def test_zpad_restores_a_stripped_leading_zero():
    out = normalise._zpad(pd.Series(["1890", "501", "75024"]))
    assert out.tolist() == ["01890", "00501", "75024"]


def test_zpad_survives_integer_typed_input():
    # The exact defect: a column that reached pandas as int64.
    out = normalise._zpad(pd.Series([1890, 501], dtype="int64"))
    assert out.tolist() == ["01890", "00501"]


def test_zpad_trims_whitespace_before_padding():
    # Fixed-width publisher files pad with spaces; ' 1890' zfilled without a
    # strip gives '01890'-shaped garbage of the wrong width.
    out = normalise._zpad(pd.Series([" 1890", "2135 "]))
    assert out.tolist() == ["01890", "02135"]
    assert (out.str.len() == 5).all()


def test_zpad_honours_a_narrower_width_for_fips():
    assert normalise._zpad(pd.Series(["1", "48"]), 2).tolist() == ["01", "48"]
    assert normalise._zpad(pd.Series(["1", "201"]), 3).tolist() == ["001",
                                                                    "201"]


def test_zpad_never_truncates_an_overlong_code():
    # Silent truncation would be worse than a stripped zero: it fabricates a
    # valid-looking code that belongs to a different place.
    assert normalise._zpad(pd.Series(["123456"])).tolist() == ["123456"]


# ---------------------------------------------------------------------------
# gazetteer
# ---------------------------------------------------------------------------
GAZ = (
    "GEOID\tALAND\tAWATER\tALAND_SQMI\tAWATER_SQMI\tINTPTLAT\tINTPTLONG"
    "               \n"
    "01890\t1000\t20\t10.5\t0.2\t42.4526\t-71.1469\n"
    "1890x\t1\t0\t0.1\t0.0\t1.0\t-1.0\n"
    "75024\t2000\t0\t20.0\t0.0\t33.0198\t-96.6989\n"
)


def test_gazetteer_keeps_the_leading_zero_and_types_the_numerics(write_zip):
    write_zip("gaz_zcta", "2020_gaz_zcta_national.txt", GAZ)
    out = normalise.gazetteer()
    assert out["zcta"].tolist() == ["01890", "1890x", "75024"]
    assert out["land_area_sqmi"].dtype.kind == "f"
    assert out["land_area_sqmi"].iloc[0] == 10.5
    assert out["longitude"].iloc[0] == pytest.approx(-71.1469)


def test_gazetteer_strips_the_trailing_spaces_in_the_intptlong_header(
        write_zip):
    # The real file ships INTPTLONG padded with ~100 spaces. Without the
    # header strip the rename misses and longitude is dropped entirely — the
    # cost model then has no geometry and every line haul is the default.
    write_zip("gaz_zcta", "gaz.txt", GAZ)
    assert "longitude" in normalise.gazetteer().columns


def test_gazetteer_raises_rather_than_returning_an_empty_frame(data_root):
    with pytest.raises(FileNotFoundError, match="ingest.acquire"):
        normalise.gazetteer()


# ---------------------------------------------------------------------------
# CBP
# ---------------------------------------------------------------------------
CBP = ("zip,est,emp,ap,stabbr,cty_name\n"
       "01890,120,900,45000,MA,Middlesex\n"
       "1890,5,10,100,XX,Bogus\n"
       "75024,300,2500,180000,TX,Collin\n")


def test_cbp_keeps_the_leading_zero_and_renames_to_the_house_schema(write_zip):
    write_zip("cbp_zip", "zbp22totals.txt", CBP)
    out = normalise.cbp()
    assert out["zcta"].tolist() == ["01890", "01890", "75024"]
    assert "establishments" in out.columns and "est" not in out.columns
    assert out["establishments"].dtype.kind in "if"
    assert out["employment"].iloc[0] == 900


def test_cbp_coerces_a_publisher_sentinel_to_nan_not_zero(write_zip):
    # CBP uses blanks and 'D' (disclosure-suppressed) in numeric columns.
    # Coercing those to 0 would say "no businesses here", which is a
    # substantive claim about the place rather than a missing value.
    write_zip("cbp_zip", "z.txt", "zip,est,emp,ap\n01890,D,,45000\n")
    out = normalise.cbp()
    assert pd.isna(out["establishments"].iloc[0])
    assert pd.isna(out["employment"].iloc[0])
    assert out["annual_payroll"].iloc[0] == 45000


# ---------------------------------------------------------------------------
# ZCTA -> county crosswalk
# ---------------------------------------------------------------------------
XWALK = (
    "﻿GEOID_ZCTA5_20|GEOID_COUNTY_20|AREALAND_PART\n"
    "01890|25017|900\n"
    "01890|25009|100\n"
    "2135|25025|500\n"
    "|25027|700\n"
)


def test_zcta_county_pads_both_keys_and_handles_the_bom(data_root):
    folder = paths.RAW / "zcta_county_xwalk"
    folder.mkdir(parents=True)
    (folder / "x.txt").write_text(XWALK, encoding="utf-8")
    out = normalise.zcta_county()
    # A BOM left on the first header turns 'GEOID_ZCTA5_20' into
    # '﻿GEOID_ZCTA5_20' and the startswith() lookup raises StopIteration.
    assert set(out["zcta"]) == {"01890", "02135"}
    assert (out["county_geoid"].str.len() == 5).all()


def test_zcta_county_keeps_the_county_sharing_the_most_land(data_root):
    folder = paths.RAW / "zcta_county_xwalk"
    folder.mkdir(parents=True)
    (folder / "x.txt").write_text(XWALK, encoding="utf-8")
    out = normalise.zcta_county().set_index("zcta")
    # 01890 straddles two counties; assigning it arbitrarily would move a
    # whole ZCTA's permits and wages to the wrong metro.
    assert out.loc["01890", "county_geoid"] == "25017"
    assert len(out) == out.index.nunique(), "one row per ZCTA"


def test_zcta_county_drops_county_rows_with_no_zcta_intersection(data_root):
    folder = paths.RAW / "zcta_county_xwalk"
    folder.mkdir(parents=True)
    (folder / "x.txt").write_text(XWALK, encoding="utf-8")
    out = normalise.zcta_county()
    assert "00000" not in set(out["zcta"])
    assert len(out) == 2


# ---------------------------------------------------------------------------
# Zillow ZORI (wide -> long)
# ---------------------------------------------------------------------------
def test_zillow_zori_melts_to_long_and_keeps_the_leading_zero(data_root):
    folder = paths.EXTERNAL / "zillow_zori"
    folder.mkdir(parents=True)
    pd.DataFrame({
        "RegionID": [1, 2], "RegionName": ["01890", "75024"],
        "Metro": ["Boston", "Dallas"], "CountyName": ["Middlesex", "Collin"],
        "State": ["MA", "TX"],
        "2023-01-31": [2500.0, 1800.0], "2023-02-28": [None, 1810.0],
    }).to_csv(folder / "zori.csv", index=False)

    out = normalise.zillow_zori()
    assert set(out["zcta"]) == {"01890", "75024"}
    # The NaN month must be dropped, not carried as a zero rent — a zero
    # would show up as a -100% year-on-year change in the panel.
    assert len(out) == 3
    assert out["rent_index"].notna().all()
    assert out["year"].unique().tolist() == [2023]
    assert out.loc[out.zcta == "01890", "metro"].iloc[0] == "Boston"


def test_zillow_zori_raises_with_the_acquisition_guide_reference(data_root):
    with pytest.raises(FileNotFoundError, match="ACQUISITION_GUIDE"):
        normalise.zillow_zori()


# ---------------------------------------------------------------------------
# OMB delineation
# ---------------------------------------------------------------------------
def test_cbsa_county_builds_a_five_digit_geoid_from_split_fips(data_root):
    folder = paths.RAW / "cbsa_county"
    folder.mkdir(parents=True)
    frame = pd.DataFrame({
        "CBSA Code": ["14460", "19100", None],
        "CBSA Title": ["Boston", "Dallas", None],
        "CSA Title": ["Boston-Worcester", "Dallas-Fort Worth", None],
        "Metropolitan/Micropolitan Statistical Area":
            ["Metropolitan Statistical Area",
             "Metropolitan Statistical Area", None],
        "FIPS State Code": ["25", "48", None],
        "FIPS County Code": ["017", "85", None],
        "County/County Equivalent": ["Middlesex", "Denton", None],
        "Central/Outlying County": ["Central", "Outlying", None],
    })
    with pd.ExcelWriter(folder / "list1.xlsx") as xl:
        pd.DataFrame([["title"], ["subtitle"]]).to_excel(
            xl, index=False, header=False)
        frame.to_excel(xl, index=False, startrow=2)

    out = normalise.cbsa_county()
    # '48' + '85' must become 48085, not 4885 — a county GEOID that exists
    # and belongs to somewhere else entirely.
    assert out["county_geoid"].tolist() == ["25017", "48085"]
    assert (out["county_geoid"].str.len() == 5).all()
    assert out["is_metro"].tolist() == [True, True]
    # The footnote block after the data must not become a row.
    assert len(out) == 2


# ---------------------------------------------------------------------------
# the driver
# ---------------------------------------------------------------------------
def test_run_skips_an_unacquired_source_and_normalises_the_rest(write_zip):
    """One missing download must not abort L1.

    The skip has to be recorded, though: a source silently absent from
    data/interim becomes a column of NULLs across the whole panel two layers
    later, and nothing there knows why.
    """
    write_zip("cbp_zip", "z.txt", CBP)
    results = {r["source"]: r for r in normalise.run(["cbp", "gazetteer"])}

    assert results["cbp"]["status"] == "ok"
    assert results["cbp"]["rows"] == 3
    assert (paths.INTERIM / "cbp.parquet").exists()

    assert results["gazetteer"]["status"] == "skipped"
    assert "ingest.acquire" in results["gazetteer"]["reason"]
    assert not (paths.INTERIM / "gazetteer.parquet").exists()


def test_run_writes_parquet_that_preserves_the_padded_codes(write_zip):
    # Parquet keeps dtypes, but only if the frame handed to it is already
    # string-typed. A round trip is the only way to prove it.
    write_zip("cbp_zip", "z.txt", CBP)
    normalise.run(["cbp"])
    back = pd.read_parquet(paths.INTERIM / "cbp.parquet")
    assert back["zcta"].tolist() == ["01890", "01890", "75024"]
    assert back["zcta"].dtype.kind not in "iuf", (
        "the code round-tripped as a number and lost its leading zero")


def test_every_normaliser_declares_a_grain_key():
    # run() logs `nunique(key)`; a key that is not a column logs '-' and the
    # only sanity check on the file's grain is lost.
    assert set(normalise.NORMALISERS) == {
        "gazetteer", "cbp", "building_permits", "zcta_county",
        "cbsa_county", "zillow_zori"}
    for name, (fn, key) in normalise.NORMALISERS.items():
        assert callable(fn), name
        assert key in {"zcta", "county_geoid"}, name
