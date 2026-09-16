"""Single source of random seeds.

Nothing in this project hardcodes a seed. Changing one is a deliberate act
recorded in reproducibility/seeds.toml and visible in review.
"""

from __future__ import annotations

from functools import lru_cache

try:                                    # 3.11+
    import tomllib
except ModuleNotFoundError:             # 3.9 / 3.10
    import tomli as tomllib
from pathlib import Path

SEEDS_FILE = (Path(__file__).resolve().parents[3]
              / "reproducibility" / "seeds.toml")


@lru_cache(maxsize=1)
def _seeds() -> dict:
    """Parse reproducibility/seeds.toml once and cache it.

    Cached because every stage asks for a seed and the file is the one
    place a seed may live; re-reading it mid-run could also hand two
    stages different values for the same name.
    """
    with open(SEEDS_FILE, "rb") as fh:
        return tomllib.load(fh)


def seed(section: str, name: str) -> int:
    """Return the seed for one step, e.g. seed("models", "hazard")."""
    try:
        return int(_seeds()[section][name])
    except KeyError as exc:
        raise KeyError(
            f"no seed for [{section}].{name} in {SEEDS_FILE}; add it rather "
            f"than hardcoding a value"
        ) from exc
