"""Seeds must come from the manifest, and missing ones must fail loudly."""

import duckdb
import pytest

from siting_atlas.common.seeds import seed
from siting_atlas.warehouse.schema import build_dim_scenario


def test_known_seed_resolves():
    assert isinstance(seed("models", "hazard"), int)


def test_missing_seed_raises_with_guidance():
    with pytest.raises(KeyError, match="rather than hardcoding"):
        seed("models", "does_not_exist")


def test_warehouse_reads_the_manifest_rather_than_a_literal():
    """The one place a seed is written to disk must come from the manifest.

    Until this test existed, seeds.toml was read by nothing but its own unit
    test while `dim_scenario` — the table whose entire purpose is to record
    the seed a published number was produced under — carried a hardcoded
    20240101 that matched no entry in the manifest. A manifest nothing reads
    is documentation, not reproducibility.
    """
    db = duckdb.connect(":memory:")
    build_dim_scenario(db)
    stored = db.execute("SELECT seed FROM dim_scenario").fetchone()[0]
    assert stored == seed("global", "seed")
