"""Tests for the pilot metro crosswalk.

The point of the crosswalk is that a bad join would not raise — it would
change the sample and stay silent. So these tests assert the specific
near-misses the real data produces, not just that lookup works.
"""

from __future__ import annotations

import pandas as pd
import pytest

from siting_atlas.common.metros import PILOT, REGISTRY, Metro, MetroRegistry

# CBSA titles that changed between the 2020 delineation Zillow still publishes
# and the 2023 delineation this project uses. A title join drops all six.
RENAMED = {
    "41860": ("San Francisco-Oakland-Berkeley, CA",
              "San Francisco-Oakland-Fremont, CA"),
    "35620": ("New York-Newark-Jersey City, NY-NJ-PA",
              "New York-Newark-Jersey City, NY-NJ"),
    "16980": ("Chicago-Naperville-Elgin, IL-IN-WI",
              "Chicago-Naperville-Elgin, IL-IN"),
    "12420": ("Austin-Round Rock-Georgetown, TX",
              "Austin-Round Rock-San Marcos, TX"),
    "19740": ("Denver-Aurora-Lakewood, CO", "Denver-Aurora-Centennial, CO"),
    "33100": ("Miami-Fort Lauderdale-Pompano Beach, FL",
              "Miami-Fort Lauderdale-West Palm Beach, FL"),
}


def fake_delineation() -> pd.DataFrame:
    """The 2023-titled delineation, plus decoys a name match would catch."""
    rows = [{"cbsa_code": c, "cbsa_title": RENAMED[c][1]} for c in RENAMED]
    rows += [{"cbsa_code": code, "cbsa_title": title} for code, title in (
        ("41940", "San Jose-Sunnyvale-Santa Clara, CA"),
        ("42660", "Seattle-Tacoma-Bellevue, WA"),
        ("34980", "Nashville-Davidson--Murfreesboro--Franklin, TN"),
        ("38060", "Phoenix-Mesa-Chandler, AZ"),
        ("14260", "Boise City, ID"),
        ("10940", "Austin, MN"),            # the Austin decoy
        ("35100", "New Bern, NC"),          # the New York decoy
        ("42220", "Santa Rosa-Petaluma, CA"),   # Bay Area, deliberately out
    )]
    return pd.DataFrame(rows)


def test_every_pilot_code_survives_a_title_rename():
    """Six of ten titles changed. Keying on the code is why nothing broke."""
    d = fake_delineation()
    report = REGISTRY.validate(d)
    assert report["ok"], report["missing"]

    for code, (old_title, new_title) in RENAMED.items():
        assert REGISTRY.for_code(code) is not None
        assert old_title != new_title, "fixture should encode a real rename"
        # The old title is nowhere in the delineation, so a title join fails.
        assert old_title not in set(d.cbsa_title)


def test_decoy_metros_are_not_in_the_pilot():
    """Austin, MN and New Bern, NC are what substring matching returns."""
    assert REGISTRY.for_code("10940") is None       # Austin, MN
    assert REGISTRY.for_code("35100") is None       # New Bern, NC


def test_austin_resolves_to_texas_not_minnesota():
    assert REGISTRY.get("austin").cbsa_codes == ("12420",)
    assert REGISTRY.for_code("10940") is None


def test_bay_area_is_composite_and_excludes_santa_rosa():
    bay = REGISTRY.get("San Francisco Bay Area")
    assert bay.is_composite
    assert bay.cbsa_codes == ("41860", "41940")
    for code in bay.cbsa_codes:
        assert REGISTRY.for_code(code) is bay
    # Documented judgement call, asserted so a change is deliberate.
    assert REGISTRY.for_code("42220") is None


def test_lookup_by_slug_and_label_agree():
    assert REGISTRY.get("bay_area") is REGISTRY.get("San Francisco Bay Area")
    assert REGISTRY.get("NASHVILLE") is REGISTRY.get("nashville")


def test_unknown_key_raises_with_the_known_list():
    with pytest.raises(KeyError, match="not a pilot metro"):
        REGISTRY.get("Cleveland")


def test_heldout_split_is_disjoint_and_complete():
    fit, held = REGISTRY.fit_codes, REGISTRY.heldout_codes
    assert set(fit).isdisjoint(held)
    assert set(fit) | set(held) == set(REGISTRY.codes())
    assert set(held) == {"38060", "14260"}          # Phoenix, Boise


def test_no_cbsa_belongs_to_two_metros():
    """A county in two pilot metros would be double-counted everywhere."""
    with pytest.raises(ValueError, match="cannot belong to two"):
        MetroRegistry([Metro("a", "A", ("16980",)),
                       Metro("b", "B", ("16980",))])


def test_duplicate_slug_raises():
    with pytest.raises(ValueError, match="duplicate metro slug"):
        MetroRegistry([Metro("x", "X", ("11111",)),
                       Metro("x", "Y", ("22222",))])


def test_validate_flags_a_retired_cbsa():
    """An OMB merge must surface, not shrink the sample quietly."""
    d = fake_delineation()
    report = REGISTRY.validate(d[d.cbsa_code != "14260"])
    assert not report["ok"]
    assert report["missing"] == ["14260"]


def test_counties_are_tagged_with_the_metro_name():
    got = REGISTRY.counties(fake_delineation())
    assert set(got.metro_slug) == {m.slug for m in PILOT}
    bay = got[got.cbsa_code.isin(["41860", "41940"])]
    assert set(bay.metro_label) == {"San Francisco Bay Area"}


def test_counties_can_be_filtered_to_the_fitting_sample():
    held = REGISTRY.counties(fake_delineation(), heldout=True)
    assert set(held.metro_slug) == {"phoenix", "boise"}
    fit = REGISTRY.counties(fake_delineation(), heldout=False)
    assert "phoenix" not in set(fit.metro_slug)


def test_pilot_matches_the_configured_metro_names():
    """config.PILOT_METROS and this module must not drift apart."""
    from siting_atlas.common import config
    assert {m.label for m in PILOT} == set(config.PILOT_METROS)
    assert {m.label for m in PILOT if m.heldout} == set(config.HELDOUT_METROS)
