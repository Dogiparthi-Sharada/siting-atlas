"""Configuration and credential loading.

Credentials come from the environment. A ``.env`` file at the repo root is
loaded automatically so a developer does not have to export variables in
every shell — it is gitignored and never read into a log.

Everything else the pipeline needs to be told (vintages, the metro list,
modelling constants) lives here rather than being scattered as literals, so
that changing scope is a one-file edit and shows up cleanly in review.
"""

from __future__ import annotations

import os
from pathlib import Path

from . import paths

# --- credentials ------------------------------------------------------------
_ENV_LOADED = False


def load_dotenv(path: Path | None = None) -> int:
    """Load KEY=VALUE lines from .env into os.environ if not already set.

    Existing environment variables always win, so CI can override the file.
    Returns the number of variables loaded. Values are never logged.
    """
    global _ENV_LOADED
    target = path or (paths.ROOT / ".env")
    if _ENV_LOADED or not target.exists():
        return 0
    loaded = 0
    for raw in target.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if value[:1] in ("'", '"'):
            end = value.find(value[0], 1)
            value = value[1:end] if end > 0 else value[1:]
        else:
            # An unquoted value stops at an inline comment. Without this,
            # `EIA_API_KEY=abc123 # prod key` sends the API the literal
            # string "abc123 # prod key" and the 403 that comes back says
            # nothing about why.
            value = value.split(" #", 1)[0].strip()
        if key and key not in os.environ:
            os.environ[key] = value
            loaded += 1
    _ENV_LOADED = True
    return loaded


# --- vintages ---------------------------------------------------------------
# Pinned deliberately. A silent vintage change is the failure mode that
# corrupts a panel without raising, so the value is stated once and asserted
# by a data contract downstream.
ACS_YEAR = 2023
CBP_YEAR = 2022
BPS_YEAR = 2023
ZCTA_VINTAGE = 2020

# --- modelling scope --------------------------------------------------------
PANEL_START_YEAR = 2018
PANEL_END_YEAR = 2025
BACKTEST_TRAIN_THROUGH = 2023      # train on openings up to and including
BACKTEST_PREDICT = (2024, 2025)    # score against these

# Ten pilot metros. Held-out metros are excluded from model fitting entirely,
# so they test geographic transfer rather than just temporal transfer.
PILOT_METROS = (
    "San Francisco Bay Area", "New York", "Chicago", "Austin", "Seattle",
    "Denver", "Miami", "Nashville", "Phoenix", "Boise",
)
HELDOUT_METROS = ("Phoenix", "Boise")

# --- ACS variables ----------------------------------------------------------
# Kept small and interpretable. Each is a level feature; rate-of-change
# features come from the monthly sources (see docs/data/README).
ACS_VARIABLES: dict[str, str] = {
    "B01003_001E": "population",
    "B19013_001E": "median_household_income",
    "B25077_001E": "median_home_value",
    "B01002_001E": "median_age",
    "B11001_001E": "households",
    "B25003_002E": "owner_occupied",
    "B25003_003E": "renter_occupied",
    "B15003_022E": "bachelors_degree",
    "B23025_002E": "in_labor_force",
    "B08201_001E": "vehicle_availability_total",
}

# Margins of error accompany every ACS estimate and are routinely discarded.
# We carry a subset through into the uncertainty model.
ACS_MOE_FOR = ("B19013_001E", "B01003_001E")


def census_key() -> str | None:
    """Census API key, or None. Loads .env on first call."""
    load_dotenv()
    return os.environ.get("CENSUS_API_KEY") or None


def require_census_key() -> str:
    """The Census key, or a RuntimeError naming how to get one.

    Used where a missing key is fatal. ``census_key()`` is the softer
    form for callers that only want to report availability.
    """
    key = census_key()
    if not key:
        raise RuntimeError(
            "CENSUS_API_KEY is not set. Add it to .env at the repo root or "
            "export it. Free key: https://api.census.gov/data/key_signup.html"
        )
    return key


def describe() -> dict:
    """Configuration snapshot written into run artefacts for provenance."""
    return {
        "acs_year": ACS_YEAR,
        "cbp_year": CBP_YEAR,
        "bps_year": BPS_YEAR,
        "zcta_vintage": ZCTA_VINTAGE,
        "panel_years": [PANEL_START_YEAR, PANEL_END_YEAR],
        "train_through": BACKTEST_TRAIN_THROUGH,
        "predict_years": list(BACKTEST_PREDICT),
        "pilot_metros": list(PILOT_METROS),
        "heldout_metros": list(HELDOUT_METROS),
        "acs_variables": len(ACS_VARIABLES),
        "census_key_present": census_key() is not None,
    }
