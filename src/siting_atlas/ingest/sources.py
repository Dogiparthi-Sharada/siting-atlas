"""The source registry: what this project reads, and what to distrust.

Split for size — the declarations are long because each records the traps a
source hides. Everything is re-exported here, so no caller changes.

    source_types.py   Availability, Grain, Source
    registry.py       the 14 SOURCES entries
    sources.py        this file: ANALYTICAL and the lookup helpers
"""

from __future__ import annotations

from .registry import BY_KEY, SOURCES
from .source_types import Availability, Grain, Source

__all__ = ["SOURCES", "ANALYTICAL", "Source", "Availability", "Grain",
           "get", "by_availability", "summary_rows"]


ANALYTICAL = tuple(s for s in SOURCES if s.key != "osm")


def get(key: str) -> Source:
    """Look up one registered source by key, or raise naming the valid ones.

    ``from None`` suppresses the KeyError chain: the useful message is the
    list of known keys, not the dict lookup that failed to find one.
    """
    try:
        return BY_KEY[key]
    except KeyError:
        raise KeyError(
            f"unknown source {key!r}; known: {', '.join(sorted(BY_KEY))}"
        ) from None


def by_availability(status: Availability) -> tuple[Source, ...]:
    """Every source in one availability state (OPEN, KEYED, BLOCKED, MANUAL).

    Used by the acquire CLI to decide what it can even attempt, and by the
    docs generator to group the acquisition table.
    """
    return tuple(s for s in SOURCES if s.availability is status)


def summary_rows() -> list[tuple[str, ...]]:
    """Rows for the acquisition-status table printed by the CLI and docs."""
    return [
        (s.key, s.title, s.grain.value, s.availability.value,
         s.key_env or "-", "yes" if s.usable else "no")
        for s in SOURCES
    ]
