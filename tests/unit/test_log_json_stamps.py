"""A stamp must describe the write, never the payload.

`write_json` spread `**payload` after the two stamp keys, so an emitter that
resumes by reading its own artefact back in -- `covariate_harness.load` does
exactly this -- carried the previous run's `run_id` and its first-write
`written_at` forward for ever. Two materially different versions of
`covariate_search.json` shipped under one identical stamp before it was caught
on 2026-09-16.

The fix is three lines and easy to undo by accident, and nothing failed while
the bug was live. Hence this test.
"""

from __future__ import annotations

import json

from siting_atlas.common.log_json import read_json, write_json


def test_payload_stamps_do_not_shadow_fresh_ones(tmp_path):
    stale = {
        "run_id": "STALE-RUN-ID",
        "written_at": "1999-01-01T00:00:00+00:00",
        "facilities": 687,
    }
    p = write_json(tmp_path / "artefact.json", dict(stale))
    got = read_json(p)

    assert got["run_id"] != "STALE-RUN-ID", (
        "a run_id carried in the payload shadowed the fresh one -- the "
        "`**payload` spread is back before the stamp keys")
    assert not got["written_at"].startswith("1999"), (
        "written_at came from the payload rather than from this write")
    assert got["facilities"] == 687, "the rest of the payload must survive"


def test_resume_by_reload_restamps_from_the_live_context(tmp_path):
    """The resume path, which is how the bug actually reached production.

    Two writes inside one process SHOULD share a `run_id` -- that is what a run
    identifier means, and asserting otherwise was this test's first mistake.
    The property that matters is narrower: when an emitter reads its own
    artefact back and writes it out again, the stamp must come from the live
    context rather than from the bytes it just read.
    """
    from siting_atlas.common import context

    first = read_json(write_json(tmp_path / "a.json", {"facilities": 687}))
    # Simulate the artefact having been written by an EARLIER run.
    first["run_id"] = "SOME-OLDER-RUN"
    first["written_at"] = "1999-01-01T00:00:00+00:00"

    second = read_json(write_json(tmp_path / "b.json", first))
    assert second["run_id"] == context.run_id(), (
        "resume-by-reload kept the artefact's own run_id instead of the "
        "live one")
    assert second["written_at"] != "1999-01-01T00:00:00+00:00"
    assert second["facilities"] == 687


def test_stamp_keys_are_first_so_the_file_reads_well(tmp_path):
    p = write_json(tmp_path / "c.json", {"z": 1, "facilities": 687})
    keys = list(json.loads(p.read_text()).keys())
    assert keys[:2] == ["run_id", "written_at"]
