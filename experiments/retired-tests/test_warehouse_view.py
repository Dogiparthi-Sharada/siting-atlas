"""Tests for the WarehouseView implemented against a real DuckDB file.

The one that matters most is ``test_radius_is_kilometres_not_miles``. The
Protocol speaks kilometres, the project's distance function returns miles,
and a missing conversion produces a perfectly plausible set of neighbours
that is simply the wrong size. Nothing raises, nothing looks odd, and gate 5
silently checks the wrong area.

Each test builds a throwaway warehouse with four ZCTAs at real centroids, so
every distance below is checkable by hand.

The last section reaches through ``agent.runner.run`` rather than calling the
view directly. It belongs here because it is the same defect seen from the
other end: whether a missing warehouse becomes a recorded REJECT or a
traceback is a property of this file, but it is only observable there.
"""

from __future__ import annotations

import json

import duckdb
import pytest

from siting_atlas.agent.runner import run
from siting_atlas.agent.types import Mutation
from siting_atlas.agent.warehouse_view import KM_PER_MILE, DuckDBWarehouseView
from siting_atlas.common import paths
from siting_atlas.cost.daganzo import haversine_miles

# Plano and its neighbours, with real centroids. The distances between them
# are small and known, which is what makes the radius assertions meaningful.
ZCTAS = [
    ("75024", 33.0755, -96.8100),    # Plano  - the mutation target
    ("75025", 33.0830, -96.7500),    # Plano  - ~5.6 km east
    ("75080", 32.9750, -96.7500),    # Richardson - ~12.9 km south-east
    ("94608", 37.8380, -122.2870),   # Emeryville CA - ~2,300 km away
]


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


@pytest.fixture
def view(warehouse, tmp_path):
    return DuckDBWarehouseView(warehouse, donor_pool={"75025", "75080"},
                               audit_dir=tmp_path / "audit")


@pytest.fixture(autouse=True)
def no_real_panel(tmp_path, monkeypatch):
    """Point every test at an absent panel unless it says otherwise.

    Without this these tests would assert against whatever
    ``data/processed/panel.parquet`` happens to contain, so they would pass
    today and start failing on the day the facility data lands — for the
    wrong reason. Pinning the input makes each test say which world it is
    describing.
    """
    monkeypatch.setattr(paths, "PANEL", tmp_path / "absent-panel.parquet")


def make_mutation(**overrides) -> Mutation:
    base = dict(  # noqa: C408 - matches the helper in test_gates.py
        mutation_id="test-0001", operator="Walmart", facility_type="SC",
        zcta="75024", latitude=33.0198, longitude=-96.6989,
        open_year=2025, open_quarter=1, confidence=0.94,
        source_text="Walmart opens a new sortation centre in Plano, Texas.",
        source_url="https://example.com/newsroom/plano")
    base.update(overrides)
    return Mutation(**base)



# ---------------------------------------------------------------------------
# geography
# ---------------------------------------------------------------------------
def test_zcta_exists_reads_the_real_dimension(view):
    assert view.zcta_exists("75024")
    assert not view.zcta_exists("00000")


def test_radius_is_kilometres_not_miles(view):
    """The unit trap, pinned against a hand-checked distance.

    75025 sits about 5.6 km from 75024. A radius of 6 must include it and a
    radius of 5 must not. If the implementation forgot to convert, 6 "km"
    would actually mean 6 miles = 9.7 km and both assertions would still
    pass — so the test also checks the boundary from the other side, at a
    radius where miles and kilometres disagree about the answer.
    """
    d_miles = float(haversine_miles(33.0755, -96.8100, 33.0830, -96.7500))
    d_km = d_miles * KM_PER_MILE
    assert 5.0 < d_km < 6.5, f"fixture drifted: 75024-75025 is {d_km:.2f} km"

    assert "75025" in view.neighbours_within("75024", d_km + 0.1)
    assert "75025" not in view.neighbours_within("75024", d_km - 0.1)
    # The discriminating case: 4 km excludes it, but 4 miles (6.4 km) would
    # include it. Only a correct conversion gets this right.
    assert "75025" not in view.neighbours_within("75024", 4.0)


def test_neighbours_exclude_the_query_zcta(view):
    """Gate 5 tests is_donor(m.zcta) separately; counting the ZCTA as its
    own neighbour would report the same problem twice under two names."""
    assert "75024" not in view.neighbours_within("75024", 50.0)


def test_neighbours_scale_with_the_radius(view):
    assert view.neighbours_within("75024", 1.0) == set()
    assert view.neighbours_within("75024", 20.0) == {"75025", "75080"}
    # Emeryville is 2,300 km away and must not appear until the radius is
    # absurd — a sign error in the haversine would bring it in early.
    assert "94608" not in view.neighbours_within("75024", 1_000.0)
    assert "94608" in view.neighbours_within("75024", 3_000.0)


def test_unknown_zcta_returns_empty_rather_than_raising(view):
    """A gate must report, never explode."""
    assert view.neighbours_within("99999", 50.0) == set()


def test_missing_warehouse_degrades_instead_of_raising_into_a_gate(tmp_path):
    """``Gate.check`` promises it "must not raise for ordinary failures".

    An unbuilt warehouse is the most ordinary failure there is: it is the
    state of a fresh clone. Raising FileNotFoundError out of ``zcta_exists``
    put that traceback through gate 2 and out of the whole pipeline, so the
    run died before the audit record was written — losing the record of the
    refused write, which is the one artefact the safety claim rests on.
    Every Protocol method therefore degrades to "I know of no ZCTAs", which
    makes gate 2 reject cleanly instead.
    """
    v = DuckDBWarehouseView(tmp_path / "absent.duckdb",
                            audit_dir=tmp_path / "audit")
    assert v.zcta_exists("75024") is False
    assert v.neighbours_within("75024", 50.0) == set()
    assert v.donor_pool() == set()
    assert "warehouse.schema" in v.warehouse_error


def test_the_actionable_error_survives_for_a_direct_caller(tmp_path):
    """Degrading gracefully must not delete the message saying how to fix it.

    A gate has to keep going; a human running this by hand has to be told
    which command builds the thing that is missing.
    """
    v = DuckDBWarehouseView(tmp_path / "absent.duckdb")
    with pytest.raises(FileNotFoundError, match="warehouse.schema"):
        v._load_centroids()


def test_describe_still_works_when_the_warehouse_is_missing(tmp_path):
    """The audit record must be writable precisely when something is wrong.

    ``describe()`` guarded ``zctas`` on ``db_path.exists()`` and then asked
    for ``donor_pool_size`` on the next line, which went straight back to
    the database — so the guard bought nothing and the record could not be
    written at all. ``warehouse_error`` is what separates "read a warehouse
    with no ZCTAs in it" from "could not read the warehouse".
    """
    v = DuckDBWarehouseView(tmp_path / "absent.duckdb",
                            audit_dir=tmp_path / "audit")
    described = v.describe()
    assert described["warehouse_exists"] is False
    assert described["zctas"] == 0
    assert described["donor_pool_size"] == 0
    assert "warehouse.schema" in described["warehouse_error"]


# ---------------------------------------------------------------------------
# donor pool
# ---------------------------------------------------------------------------
def test_explicit_donor_pool_is_used_verbatim(view):
    assert view.donor_pool() == {"75025", "75080"}
    assert view.is_donor("75025")
    assert not view.is_donor("75024")
    assert view.donor_pool_basis == "explicit"


def test_unidentifiable_donor_pool_falls_back_to_the_whole_universe(
        warehouse, tmp_path):
    """With no target variable there is no way to know who is untreated.

    Every ZCTA therefore counts as a nominal donor and gate 5 escalates
    everything. That is the intended fail-safe: a gate that passes when it
    has nothing to check hands out a green tick meaning "not examined".
    """
    v = DuckDBWarehouseView(warehouse, audit_dir=tmp_path / "audit")
    assert v.donor_pool() == {z[0] for z in ZCTAS}
    assert v.donor_pool_basis == "undetermined-universe"
    assert v.is_donor("75024"), "the mutation target is a nominal donor"


def test_audit_writability_is_probed_not_assumed(tmp_path, warehouse):
    v = DuckDBWarehouseView(warehouse, audit_dir=tmp_path / "audit")
    assert v.audit_log_writable()
    assert not (tmp_path / "audit" / ".write_probe").exists()

    blocked = tmp_path / "blocked"
    blocked.mkdir(mode=0o500)
    try:
        v2 = DuckDBWarehouseView(warehouse, audit_dir=blocked / "audit")
        assert not v2.audit_log_writable()
    finally:
        blocked.chmod(0o700)


def test_describe_records_the_state_gates_ran_against(view):
    d = view.describe()
    assert d["zctas"] == len(ZCTAS)
    assert d["donor_pool_basis"] == "explicit"
    assert d["donor_pool_size"] == 2


# ---------------------------------------------------------------------------
# the gate contract, through the runner that has to honour it
# ---------------------------------------------------------------------------
def test_a_missing_warehouse_is_rejected_and_recorded_not_raised(tmp_path):
    """The degraded view, proved end to end rather than in isolation.

    ``Gate.check`` says a gate "must not raise for ordinary failures", and
    an unbuilt warehouse is the ordinary state of a fresh clone. Gate 2 used
    to let a FileNotFoundError out of ``zcta_exists``, which killed ``run()``
    before ``write_audit_record`` and produced a traceback where the system
    should have produced a refusal. A refused write with no record is the
    one outcome this pipeline may never have, so the assertion that matters
    below is that the audit file exists at all.
    """
    decision, path = run(make_mutation(mutation_id="no-warehouse-0001"),
                         donor_pool=set(),
                         db_path=tmp_path / "absent.duckdb",
                         audit_dir=tmp_path / "audit")

    assert decision.rejected
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["results"][-1]["gate"] == 2, "rejected at geocoding"
    state = record["warehouse_state"]
    assert state["warehouse_exists"] is False
    # Without this the record would say only "0 ZCTAs", which is also what a
    # warehouse that was read successfully and happens to be empty says.
    assert "warehouse.schema" in state["warehouse_error"]


# ---------------------------------------------------------------------------
# against the real warehouse, when it is present
# ---------------------------------------------------------------------------
@pytest.mark.integration
@pytest.mark.skipif(not paths.WAREHOUSE.exists(),
                    reason="needs the built warehouse")
def test_real_warehouse_neighbours_are_plausible():
    """A sanity check on live data: the radius must behave monotonically
    and return a believable count for a dense metro ZCTA."""
    v = DuckDBWarehouseView(donor_pool=set())
    assert v.zcta_exists("75024")

    near = v.neighbours_within("75024", 10.0)
    far = v.neighbours_within("75024", 30.0)
    assert near < far, "a larger radius must be a superset"
    assert 5 <= len(near) <= 60, f"{len(near)} neighbours within 10 km"
    assert "75024" not in far
