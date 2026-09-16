"""Run id and layer/stage propagation.

Every log record, SQL statement, shell command and HTTP request is stamped
from here. If the stamp is wrong the logs are not merely unhelpful, they are
misleading: a line attributed to L1 that came from L3 sends a post-mortem to
the wrong module. Nothing raises when that happens, so it is tested.
"""

from __future__ import annotations

import concurrent.futures
import os
import re
import threading

import pytest

from siting_atlas.common import context


@pytest.fixture(autouse=True)
def isolate_run_id(monkeypatch):
    """Each test starts from a clean contextvar and a clean environment."""
    monkeypatch.delenv("SITING_ATLAS_RUN_ID", raising=False)
    token = context._run_id.set("")
    yield
    context._run_id.reset(token)


# ---------------------------------------------------------------------------
# run id
# ---------------------------------------------------------------------------
def test_new_run_id_is_sortable_and_unique():
    a, b = context.new_run_id(), context.new_run_id()
    # YYYYmmdd-HHMMSS-xxxx: the timestamp prefix is what makes `ls logs/`
    # chronological, and the suffix is what stops two runs started in the
    # same second from writing into one directory.
    assert re.fullmatch(r"\d{8}-\d{6}-[0-9a-f]{4}", a)
    assert a != b
    assert sorted([a, b])[0][:15] <= sorted([a, b])[1][:15]


def test_init_run_adopts_an_explicit_id_and_exports_it():
    assert context.init_run("20240101-000000-abcd") == "20240101-000000-abcd"
    assert context.run_id() == "20240101-000000-abcd"
    # Exported so a shell script can chain several python invocations into
    # one logical run; without it each writes to its own logs/run-* dir.
    assert os.environ["SITING_ATLAS_RUN_ID"] == "20240101-000000-abcd"


def test_init_run_honours_an_inherited_run_id(monkeypatch):
    monkeypatch.setenv("SITING_ATLAS_RUN_ID", "inherited-0001")
    assert context.init_run() == "inherited-0001"


def test_an_explicit_id_beats_the_environment(monkeypatch):
    monkeypatch.setenv("SITING_ATLAS_RUN_ID", "inherited-0001")
    assert context.init_run("explicit-0002") == "explicit-0002"


def test_run_id_is_minted_lazily_and_then_stable():
    # A module that logs before any entry point called init_run() must still
    # get a usable id, and must not get a different one on every record.
    first = context.run_id()
    assert first and context.run_id() == first


# ---------------------------------------------------------------------------
# layer and stage
# ---------------------------------------------------------------------------
def test_layer_rejects_an_unknown_code():
    # A typo'd layer would log as 'unknown' on every record in that block.
    with pytest.raises(ValueError, match="unknown layer"), \
            context.layer("L9"):
        pass
    assert context.current_layer() == "--"


def test_layer_and_stage_restore_on_exit():
    with context.layer("L1"):
        assert context.current_layer() == "L1"
        with context.layer("L3"):
            assert context.current_layer() == "L3"
        assert context.current_layer() == "L1", "inner layer leaked outward"
    assert context.current_layer() == "--"


def test_layer_restores_even_when_the_body_raises():
    """The failure path is the one that matters: after an aborted L1 the next
    stage must not still be logging itself as L1."""
    with pytest.raises(RuntimeError), context.layer("L1"), \
            context.stage("normalise:acs"):
        raise RuntimeError("boom")
    assert context.current_layer() == "--"
    assert context.current_stage() == ""


def test_snapshot_carries_the_human_readable_layer_name():
    context.init_run("20240101-000000-abcd")
    with context.layer("L2"), context.stage("build:dim_zcta"):
        snap = context.snapshot()
    assert snap == {"run_id": "20240101-000000-abcd", "layer": "L2",
                    "layer_name": "warehouse", "stage": "build:dim_zcta"}


def test_snapshot_labels_an_unmapped_layer_rather_than_raising():
    token = context._layer.set("LX")
    try:
        assert context.snapshot()["layer_name"] == "unknown"
    finally:
        context._layer.reset(token)


def test_every_declared_layer_has_a_name():
    assert set(context.LAYERS) >= {"L0", "L1", "L2", "L3", "L4", "L5", "--"}
    assert all(isinstance(v, str) and v for v in context.LAYERS.values())


# ---------------------------------------------------------------------------
# concurrency
# ---------------------------------------------------------------------------
def test_the_run_id_survives_into_a_worker_thread():
    """A threaded stage must not mint a second run id and split the logs.

    It survives only because init_run() also writes the environment; the
    contextvar itself does not cross the thread boundary.
    """
    context.init_run("20240101-000000-abcd")
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        got = list(pool.map(lambda _: context.run_id(), range(4)))
    assert set(got) == {"20240101-000000-abcd"}


def test_layer_does_not_propagate_into_a_bare_worker_thread():
    """Documents a real gap, and the reason it is not visible.

    context.py says the contextvars design keeps the stamp correct "if a
    stage is ever run concurrently". That holds for asyncio, which copies the
    context, but NOT for threading.Thread, which starts from the defaults.
    Work handed to a thread pool inside an L3 step is logged as layer '--'
    / stage '' — plausible-looking lines filed under the wrong layer.

    Callers that thread must re-enter layer()/stage() inside the worker.
    """
    context.init_run("20240101-000000-abcd")
    seen: dict = {}
    with context.layer("L3"), context.stage("build_panel"):
        thread = threading.Thread(target=lambda: seen.update(
            context.snapshot()))
        thread.start()
        thread.join()
        assert context.current_layer() == "L3"

    assert seen["layer"] == "--", (
        "if this now says L3 the gap has been closed — delete this test")
    assert seen["stage"] == ""
    assert seen["run_id"] == "20240101-000000-abcd"
