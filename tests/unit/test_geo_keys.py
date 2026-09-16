"""Connecticut's 2022 planning regions, and the join they silently broke.

Connecticut abolished its eight counties as statistical geographies in 2022.
EJScreen 2024 tracts carry the new planning-region FIPS (09110-09190); the
pinned 2020 ZCTA-to-county crosswalk carries the retired ones
(09001-09015). The county-grain join matched nothing for all 288 Connecticut
ZCTAs and, because it is a LEFT JOIN onto a dense spine, returned NULL rather
than an error. 46,080 cells, 0.9% of the panel, and nobody noticed.

``test_every_connecticut_zcta_has_its_environmental_columns`` is the one that
fails on the pre-fix panel: 288 ZCTAs, 5 columns, all NULL.
"""

from __future__ import annotations

import pandas as pd
import pytest

from siting_atlas.common import paths
from siting_atlas.warehouse.geo_keys import (
    CT_PLANNING_REGIONS,
    FIPS_STATE,
    ct_zcta_regions,
    fips_state_sql,
)

EJ_COLUMNS = ["pm25", "diesel_pm", "traffic_proximity", "low_income_pct",
              "people_of_colour_pct"]


def test_there_are_nine_planning_regions_and_they_are_ct_county_equivalents():
    assert len(CT_PLANNING_REGIONS) == 9
    assert all(f.startswith("09") and len(f) == 5
               for f in CT_PLANNING_REGIONS)
    # None of them collides with a legacy Connecticut county code, which is
    # why the broken join returned nothing rather than something wrong.
    assert not set(CT_PLANNING_REGIONS) & {
        f"090{n:02d}" for n in range(1, 16, 2)}


def test_no_two_region_names_share_a_thirty_character_prefix():
    """CBP truncates county_name to 30 characters, so the prefix match the
    bridge relies on has to be unambiguous or it will place a ZIP in the
    wrong region without saying so."""
    prefixes = {name[:30] for name in CT_PLANNING_REGIONS.values()}
    assert len(prefixes) == 9


def test_the_fips_map_still_covers_every_state_and_territory():
    assert len(FIPS_STATE) == 56
    assert FIPS_STATE["09"] == "CT"
    assert "('09','CT')" in fips_state_sql()


# ---------------------------------------------------------------------------
# the bridge
# ---------------------------------------------------------------------------
def _xwalk(*pairs):
    return pd.DataFrame({"zcta": [z for z, _ in pairs],
                         "county_geoid": [c for _, c in pairs]})


def test_a_zip_cbp_places_is_taken_from_cbp():
    out = ct_zcta_regions(
        _xwalk(("06001", "09003")),
        pd.DataFrame({"zcta": ["06001"],
                      "county_name": ["CAPITOL PLANNING REGION"]}))
    assert out.iloc[0]["county_geoid_2022"] == "09110"
    assert out.iloc[0]["region_source"] == "cbp"


def test_a_truncated_cbp_name_still_resolves():
    """'NORTHWEST HILLS PLANNING REGIO' is what CBP actually ships."""
    out = ct_zcta_regions(
        _xwalk(("06013", "09005")),
        pd.DataFrame({"zcta": ["06013"],
                      "county_name": ["NORTHWEST HILLS PLANNING REGIO"]}))
    assert out.iloc[0]["county_geoid_2022"] == "09160"


def test_a_zip_cbp_does_not_cover_falls_back_to_its_county_mode():
    """Five Connecticut ZCTAs have no CBP row because they have no business
    establishment. The fallback is computed from the ZIPs CBP does place, and
    it is labelled so the two kinds of assignment never blur."""
    cbp = pd.DataFrame({
        "zcta": ["06013", "06018", "06021", "06770"],
        "county_name": ["NORTHWEST HILLS PLANNING REGIO"] * 3
                       + ["NAUGATUCK VALLEY PLANNING REGI"]})
    out = ct_zcta_regions(
        _xwalk(("06013", "09005"), ("06018", "09005"), ("06021", "09005"),
               ("06770", "09005"), ("06758", "09005")),
        cbp).set_index("zcta")
    assert out.loc["06758", "county_geoid_2022"] == "09160"
    assert out.loc["06758", "region_source"] == "modal"
    # The majority does not overwrite the minority that CBP did place.
    assert out.loc["06770", "county_geoid_2022"] == "09140"


def test_a_crosswalk_with_no_connecticut_returns_nothing():
    out = ct_zcta_regions(_xwalk(("01890", "25017")),
                          pd.DataFrame({"zcta": [], "county_name": []}))
    assert out.empty
    assert list(out.columns) == ["zcta", "county_geoid_2022", "region_source"]


def test_a_planning_region_is_not_split_back_into_legacy_counties():
    """The bridge runs ZCTA -> region, never county -> region, because the
    two geographies do not nest: Litchfield County alone splits three ways.
    A county-grain crosswalk would be wrong for 11 of the 288 ZCTAs."""
    cbp = pd.DataFrame({
        "zcta": ["06013", "06770", "06804"],
        "county_name": ["NORTHWEST HILLS PLANNING REGIO",
                        "NAUGATUCK VALLEY PLANNING REGI",
                        "WESTERN CONNECTICUT PLANNING R"]})
    out = ct_zcta_regions(
        _xwalk(("06013", "09005"), ("06770", "09005"), ("06804", "09005")),
        cbp)
    assert out["county_geoid_2022"].nunique() == 3, (
        "one legacy county must be able to map to several regions")


# ---------------------------------------------------------------------------
# the real panel
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not paths.PANEL.exists(),
                    reason="needs a built panel; run make panel")
def test_every_connecticut_zcta_has_its_environmental_columns():
    panel = pd.read_parquet(paths.PANEL)
    ct = panel[panel["state"] == "CT"].drop_duplicates("zcta")
    assert len(ct) == 288
    for column in EJ_COLUMNS:
        assert ct[column].notna().all(), (
            f"{column} is NULL for {int(ct[column].isna().sum())} "
            f"Connecticut ZCTAs — the planning-region join is broken again")
    # Nine regions, nine county-mean values. One value would mean the bridge
    # had collapsed to a state average; 288 would mean it was not a county
    # roll-up at all.
    assert ct["pm25"].nunique() == 9


@pytest.mark.skipif(not paths.PANEL.exists(),
                    reason="needs a built panel; run make panel")
def test_no_state_loses_ejscreen_to_a_key_mismatch():
    """The states that legitimately have no EJScreen coverage are the 2024
    release's known gaps, and Connecticut is not one of them."""
    panel = pd.read_parquet(paths.PANEL).drop_duplicates("zcta")
    missing = set(panel.loc[panel["pm25"].isna(), "state"].dropna())
    assert missing <= {"AK", "HI", "PR", "GU", "VI", "MP", "AS"}


@pytest.mark.skipif(not paths.PANEL.exists(),
                    reason="needs a built panel; run make panel")
def test_every_connecticut_zcta_has_a_cbsa_and_its_wage_columns():
    """The SECOND half of the 2022 vintage break, fixed after the first.

    `optional.py` was switched to join EJScreen on `county_geoid_2022` and
    that recovered 46,080 cells. The CBSA join in `panel_sql` was left on the
    legacy `county_geoid`, so all 288 Connecticut ZCTAs still had a NULL
    `cbsa_code` and therefore NULL on every BLS wage column — the same defect,
    one join over, found only because someone went looking for the rest of it.

    Nine planning regions map onto seven CBSAs (Hartford takes 09110 and
    09130; Bridgeport-Stamford-Danbury takes 09120 and 09190), so seven is the
    number that proves the join resolved rather than collapsed.
    """
    panel = pd.read_parquet(paths.PANEL)
    ct = panel[panel["state"] == "CT"].drop_duplicates("zcta")
    assert len(ct) == 288

    assert ct["cbsa_code"].notna().all(), (
        f"cbsa_code is NULL for {int(ct['cbsa_code'].isna().sum())} of 288 "
        "Connecticut ZCTAs — the OMB delineation carries the 2022 planning "
        "regions (09110-09190) and the join is still on the legacy counties")
    assert ct["cbsa_code"].nunique() == 7

    for column in ("wage_light_truck_driver", "wage_all_occupations"):
        assert ct[column].notna().any(), (
            f"{column} is NULL for every Connecticut ZCTA, which means the "
            "wage join never found a metro to attach to")
