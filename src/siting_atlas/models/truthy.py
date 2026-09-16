"""Turning an ``enabled`` column into booleans without guessing.

Why this is not ``.astype(bool)``
---------------------------------
``pd.Series(["false"]).astype(bool)`` is ``[True]``. Python's truthiness rule
for a string is "is it non-empty", and ``"false"`` is five characters long.
Every string that is not ``""`` becomes True, so a target column that
round-tripped through a CSV as the text ``"false"`` reads back as an
all-enabled panel: the risk set truncates every unit at t=0, every one of
them then looks left-truncated, and the risk set comes back EMPTY. No
exception, no warning, no NaN — just a downstream fit on nothing, or a
provenance check reporting twelve enabled rows where the truth is one.

That failure is not hypothetical. ``data/external/facility_panel`` is
specified as a CSV, and a CSV has no boolean type. Whether the outcome
arrives as ``True``/``False``, ``1``/``0``, ``yes``/``no`` or ``t``/``f``
depends on which tool wrote it, and the honest response to a token we do not
recognise is to stop, not to pick a side.

Deliberately strict
-------------------
An unrecognised token RAISES. The tempting alternative — treat anything
unknown as False — is exactly how a mis-spelled or differently-cased flag
turns into a silently smaller event count, which is the one error class this
project is built to refuse. A loud failure costs someone ten minutes; a quiet
one costs the whole estimate its meaning.

Numeric columns are accepted only for 0 and 1. A column holding 2 is not a
flag, it is a count of facilities, and coercing it to True would quietly
discard the distinction between "one opened" and "three opened".
"""

from __future__ import annotations

import numpy as np
import pandas as pd

_TRUE_TOKENS = frozenset({"true", "t", "yes", "y", "1", "1.0"})
_FALSE_TOKENS = frozenset({"false", "f", "no", "n", "0", "0.0"})


def as_boolean(values, *, column: str = "enabled",
               missing: bool = False) -> pd.Series:
    """Parse a flag column to real booleans, raising on anything ambiguous.

    ``missing`` is what a NULL becomes. It defaults to False because an
    unobserved enablement is an absence of evidence of enablement — but the
    caller is expected to have already checked that the column is not
    ENTIRELY null, because "nothing ever happened" and "we have not been told
    yet" are different worlds and only one of them is safe to fit on.
    """
    series = pd.Series(values).copy()

    if pd.api.types.is_bool_dtype(series):
        return series.fillna(missing).astype(bool)

    if pd.api.types.is_numeric_dtype(series):
        # 0/1 only. Rounding 0.9999 to True would be a kindness that hides a
        # unit-conversion mistake upstream.
        filled = series.fillna(0 if not missing else 1)
        bad = filled[~filled.isin([0, 1])]
        if len(bad):
            raise ValueError(
                f"{column!r} is numeric but holds value(s) other than 0 and "
                f"1 (e.g. {sorted(set(bad))[:5]}); that is a count, not a "
                f"flag — reduce it to a flag upstream where the meaning of "
                f"a 2 is known")
        return series.notna() & series.astype(float).eq(1)

    # Object / string / categorical. Normalise case and surrounding space,
    # because " True " from a hand-edited CSV means the same thing as "true".
    text = series.astype("object")
    known = pd.Series(np.full(len(series), False), index=series.index)
    seen_bad: set[str] = set()

    for i, raw in enumerate(text.to_numpy()):
        if raw is None or (isinstance(raw, float) and np.isnan(raw)) \
                or raw is pd.NA or raw is pd.NaT:
            known.iloc[i] = missing
            continue
        if isinstance(raw, (bool, np.bool_)):
            known.iloc[i] = bool(raw)
            continue
        token = str(raw).strip().lower()
        if token in _TRUE_TOKENS:
            known.iloc[i] = True
        elif token in _FALSE_TOKENS or token == "":
            known.iloc[i] = False
        else:
            seen_bad.add(str(raw))

    if seen_bad:
        raise ValueError(
            f"{column!r} holds {len(seen_bad)} unrecognised token(s) "
            f"(e.g. {sorted(seen_bad)[:5]}); accepted spellings are "
            f"true/false, 1/0, yes/no, t/f in any case. Refusing to guess: "
            f"astype(bool) would read every one of them as True and hand "
            f"back a silently wrong event count")
    return known.astype(bool)


def count_true(values, *, column: str = "enabled") -> int:
    """How many rows are genuinely flagged. Raises on ambiguous tokens."""
    return int(as_boolean(values, column=column).sum())
