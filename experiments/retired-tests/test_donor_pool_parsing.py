"""How the donor pool reads the panel's ``enabled`` column.

Split out of test_warehouse_view.py, which is about geography and the audit
probe. These two are about one line — the cast that turns the outcome column
into booleans — and they are the tests most likely to be the first thing that
fails on the day the real facility data lands.

That is the whole point of them. ``enabled`` is entirely NULL today, so this
code path never reaches the cast and nothing can go wrong yet. The parser is
``models.truthy.as_boolean``, shared with the risk set and the panel loader:
two different truthiness rules in one codebase is how the next version of
this bug gets in.
"""

from __future__ import annotations

import duckdb
import pandas as pd
import pytest

from siting_atlas.agent.warehouse_view import DuckDBWarehouseView
from siting_atlas.common import paths
from tests.unit.test_warehouse_view import ZCTAS


@pytest.fixture
def warehouse(tmp_path):
    """A minimal warehouse carrying only what the view actually reads."""
    path = tmp_path / "test.duckdb"
    con = duckdb.connect(str(path))
    con.execute("CREATE TABLE dim_zcta (zcta VARCHAR, latitude DOUBLE, "
                "longitude DOUBLE)")
    con.executemany("INSERT INTO dim_zcta VALUES (?, ?, ?)", ZCTAS)
    con.close()
    return path


def test_a_text_false_in_the_panel_does_not_treat_every_zcta(
        warehouse, tmp_path, monkeypatch):
    """``astype(bool)`` reads the five-character string "false" as True.

    Dangerous specifically because it cannot show itself yet. ``enabled`` is
    100% NULL today, so ``_treated_zctas`` returns None long before the cast
    matters and every test passes. The panel is specified as a CSV and a CSV
    has no boolean type, so the day the real facility file lands the column
    arrives as text — and every ZCTA reads as treated, the donor pool empties,
    and gate 5 answers "does this write contaminate a control unit?" against
    a pool containing nobody. It would pass. Nothing would say why.

    One row is genuinely enabled here and three are the text "false". A
    correct parse leaves three donors; ``astype(bool)`` leaves none.
    """
    panel = tmp_path / "panel.parquet"
    pd.DataFrame({"zcta": [z[0] for z in ZCTAS],
                  "enabled": ["true", "false", "false", "false"]}
                 ).to_parquet(panel, index=False)
    monkeypatch.setattr(paths, "PANEL", panel)

    v = DuckDBWarehouseView(warehouse, audit_dir=tmp_path / "audit")
    assert v.donor_pool() == {"75025", "75080", "94608"}
    assert v.donor_pool_basis == "derived-from-panel"
    assert not v.is_donor("75024"), "the one genuinely enabled ZCTA"


def test_an_unrecognisable_enabled_token_stops_rather_than_guesses(
        warehouse, tmp_path, monkeypatch):
    """Refusing to guess is the point of the shared parser.

    Treating an unknown token as False would turn a mis-spelled flag into a
    silently larger donor pool, which is the same class of error one step
    further along.
    """
    panel = tmp_path / "panel.parquet"
    pd.DataFrame({"zcta": [z[0] for z in ZCTAS],
                  "enabled": ["true", "false", "false", "maybe"]}
                 ).to_parquet(panel, index=False)
    monkeypatch.setattr(paths, "PANEL", panel)

    v = DuckDBWarehouseView(warehouse, audit_dir=tmp_path / "audit")
    with pytest.raises(ValueError, match="unrecognised token"):
        v.donor_pool()
