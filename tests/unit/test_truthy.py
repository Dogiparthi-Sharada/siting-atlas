"""Tests for parsing the ``enabled`` flag out of whatever a CSV hands us.

``pd.Series(["false"]).astype(bool)`` is ``[True]``. That one line is the
whole subject of this file, and it is here rather than in
``test_risk_set.py`` because the defect it guards is not about duration
models at all — it is about a column arriving as text on the day the real
facility panel lands, and being read as the opposite of what it says.

Nothing about that failure is loud. Every row reads as enabled, so every
unit looks enabled in its first quarter, so every unit looks left-truncated,
so the risk set comes back EMPTY — and an empty risk set raises nothing on
its own. The provenance check next door makes the mirror-image mistake and
declares an all-False panel to be real data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from siting_atlas.models.panel_source import real_panel_is_usable
from siting_atlas.models.risk_set import build_risk_set
from siting_atlas.models.truthy import as_boolean


def tiny_panel(enabled_at: int | None, n_quarters: int = 8,
               unit: str = "SYN-00001") -> pd.DataFrame:
    """A single unit over ``n_quarters`` quarters, enabled at one of them."""
    t = np.arange(n_quarters)
    flag = np.zeros(n_quarters, dtype=bool) if enabled_at is None \
        else t >= enabled_at
    return pd.DataFrame({"zcta": unit, "year": 2018 + t // 4,
                         "quarter": t % 4 + 1, "enabled": flag,
                         "x_demand": 0.5, "x_cost": -0.2,
                         "x_competition": 0.1})


def test_text_flags_are_parsed_not_coerced_to_true():
    """``pd.Series(["false"]).astype(bool)`` is ``[True]``.

    A CSV has no boolean type, and ``facilities.csv`` is specified as a CSV.
    If the outcome round-trips as text, ``.astype(bool)`` marks every
    non-empty string True — so every unit looks enabled in the first quarter,
    every unit looks left-truncated, and ``build_risk_set`` hands back an
    EMPTY risk set with no exception and no warning. This is the defect that
    bites on the day the real panel arrives rather than today, which is the
    worst possible day for it.
    """
    boolean = pd.concat([tiny_panel(3), tiny_panel(None, unit="SYN-00002")])
    text = boolean.copy()
    text["enabled"] = text["enabled"].map({True: "true", False: "FALSE "})

    parsed = build_risk_set(text)
    assert len(parsed) > 0, "a text-encoded panel produced an empty risk set"
    # The raw ``enabled`` column is carried through untouched and so keeps
    # its text dtype; ``t`` and ``event`` are what the estimator reads, and
    # they must not depend on how the panel spelled its booleans.
    pd.testing.assert_frame_equal(
        parsed.drop(columns=["enabled"]),
        build_risk_set(boolean).drop(columns=["enabled"]))


@pytest.mark.parametrize("true_token,false_token", [
    ("true", "false"), ("True", "False"), ("T", "F"), ("yes", "no"),
    ("1", "0"), (" y ", " n ")])
def test_the_spellings_a_csv_writer_might_choose(true_token, false_token):
    """Which of these a CSV contains depends on which tool wrote it."""
    parsed = as_boolean(pd.Series([true_token, false_token, None]))
    assert list(parsed) == [True, False, False]


def test_an_unrecognised_flag_token_raises_rather_than_guessing():
    """Refusing is the whole design. Treating an unknown token as False
    would quietly shrink the event count; treating it as True would quietly
    inflate it. Both produce a number, and neither produces a question."""
    with pytest.raises(ValueError, match="unrecognised token"):
        as_boolean(pd.Series(["true", "maybe", "false"]))
    with pytest.raises(ValueError, match="count, not a flag"):
        as_boolean(pd.Series([0, 1, 2]))


def test_an_unpopulated_text_panel_is_not_mistaken_for_real(tmp_path):
    """The provenance check is the last thing standing between a synthetic
    run and an unlabelled slide, and it was counting the string "false" as
    an enablement. A panel whose outcome is all text False must come back
    NOT usable, or the run drops the ``SYNTHETIC_`` prefix and the
    ``"synthetic": true`` stamp on the strength of nothing at all."""
    path = tmp_path / "panel.parquet"
    pd.DataFrame({"enabled": ["false"] * 11 + ["true"]}).to_parquet(path)

    usable, detail = real_panel_is_usable(path)
    assert detail["enabled_rows"] == 1, "eleven 'false' strings are not " \
                                        "eleven enablements"
    assert usable, "one genuine enablement is still one"

    all_false = tmp_path / "none.parquet"
    pd.DataFrame({"enabled": ["false"] * 12}).to_parquet(all_false)
    usable, detail = real_panel_is_usable(all_false)
    assert not usable and detail["enabled_rows"] == 0
