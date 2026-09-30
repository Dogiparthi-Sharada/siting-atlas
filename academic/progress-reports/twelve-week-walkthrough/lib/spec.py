"""The twelve weeks, assembled.

Conventions every entry obeys
-----------------------------
**Numbers are extracted, never typed.** Each entry's ``nums`` is a function
of a loader, so a page states what the artefact says on the day the page is
built. A week that quoted a figure from memory would reproduce the exact
fault this project already had to fix once in a figure — nine hand-entered
values and a fabricated confidence band, caught in its own audit.

**Mode is declared, not implied.** ``RECOMPUTE`` means the week's command
re-derives the result offline from the clone. ``INSPECT`` means it reads a
shipped artefact, because that stage needs the raw cache, three API keys,
~4 GB of downloads or ninety minutes of CPU. Both are legitimate; a reader
is entitled to know which one they are looking at before deciding whether a
number is being demonstrated or merely reported.

**The work is complete.** These twelve pace how it is PRESENTED; they are
not a claim about when anything happened. Every page prints the real
``run_id`` and build date of the artefact behind it, so the actual
chronology is on the page and can be checked.

Entry shape
-----------
``n``          1-12
``title``      short, no full stop
``question``   the one question the week answers
``mode``       RECOMPUTE | INSPECT
``runs``       plain-English description of what the command does
``artefacts``  keys under outputs/metrics/, minus the .json
``extra_json`` optional {alias: repo-relative path} for artefacts elsewhere
``dirs``       optional repo-relative directory to list instead of artefacts
``body``       the prose
``nums``       loader -> [(label, value, field path)]
``status``     the one line you say in the supervision meeting
``risk``       the blocker flagged that week, and how it was handled
``midterm``    optional flag, marks the week-6 checkpoint
``secs``       measured wall time, only where the week was actually timed
``limits``     what the week does NOT establish
``nxt``        [(repo-relative path, why read it)]
"""

from __future__ import annotations

import re

import modules_deliver
import modules_models
import modules_panel
import modules_setup

# Four files rather than one because a single spec crossed 300 lines. The
# split follows the semester's four movements, not a line count:
#   setup   (1-3)  choose the question, the method, and get the data
#   panel   (4-6)  build the target, build the table, find the finding
#   models  (7-9)  commit in advance, fit, report what came back
#   deliver (10-12) diagnose, recover, ship
WEEKS = (modules_setup.WEEKS + modules_panel.WEEKS
         + modules_models.WEEKS + modules_deliver.WEEKS)

assert [w["n"] for w in WEEKS] == list(range(1, 13)), \
    "weeks must be 1..12 in order"

# What replaces ruff's ISC004 (see ``ruff.toml``).
#
# The bug: every prose field here is wrapped across source lines, so a
# MISSING COMMA between two list elements concatenates them silently. Two
# caveats become one, a reader loses a caveat, and nothing errors.
#
# A length ceiling was tried first and DOES NOT WORK. Measured on this
# spec: the longest legitimate entry is 183 characters and the largest
# possible silent merge is 312, so any threshold that catches the worst
# merge also rejects honest prose -- and a merge of two SHORT entries lands
# near 80 characters, under every usable ceiling. It was tested by deleting
# a real comma, and it let the merge through.
#
# What works is matching the bug's signature instead of its size. Wrapped
# continuation lines always end with a space before the closing quote, so a
# merge is the one place a sentence-ending period butts straight against
# the next capital. Two invariants make that detectable everywhere:
#
#   1. every caveat starts uppercase and ends with a full stop
#   2. no prose contains a full stop immediately followed by a capital
#
# Given (1), any merge produces the pattern (2) forbids. File extensions
# and dotted module paths are lowercase after the dot, so they pass.
_DOT_CAPITAL = re.compile(r"\.[A-Z]")


def _check_prose() -> None:
    for w in WEEKS:
        for s in w["limits"]:
            if not s[:1].isupper() or not s.endswith("."):
                raise AssertionError(
                    f"week {w['n']}: a caveat must start with a capital and "
                    f"end with a full stop, so that a missing comma between "
                    f"two of them is detectable:\n  {s[:110]}")
        for s in list(w["limits"]) + [why for _, why in w["nxt"]]:
            hit = _DOT_CAPITAL.search(s)
            if hit:
                raise AssertionError(
                    f"week {w['n']}: full stop followed by a capital at "
                    f"offset {hit.start()} — almost certainly a MISSING "
                    f"COMMA that has silently merged two list items:\n"
                    f"  ...{s[max(0, hit.start() - 60):hit.start() + 60]}...")


_check_prose()


def week(n: int) -> dict:
    """The entry for week ``n``, or a clear error naming the valid range."""
    for w in WEEKS:
        if w["n"] == n:
            return w
    raise SystemExit(f"no such week: {n} (valid: 1-12)")
