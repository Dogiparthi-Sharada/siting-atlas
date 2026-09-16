"""The vocabulary a data source is described in.

Separated from the registry itself so the 14 source entries — which are long,
because each carries the provenance and the traps it hides — do not bury the
handful of types that give them meaning.
"""


from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Availability(StrEnum):
    """How a source behaves from this network, as measured."""

    OPEN = "open"              # downloads with no credential
    NEEDS_KEY = "needs_key"    # reachable, but requires a free API key
    BLOCKED = "blocked"        # reachable host, request refused (proxy/WAF)
    MANUAL = "manual"          # no stable URL; file must be placed by hand


class Grain(StrEnum):
    """Geographic or entity level one row of a source describes.

    Named rather than free text because the grain is what decides whether
    two sources can be joined at all, and a typo in a string would look
    like a new grain instead of failing.
    """
    ZCTA = "zcta"
    ZIP = "zip"
    COUNTY = "county"
    METRO = "metro"
    STATE = "state"
    REGION = "region"
    TRACT = "tract"
    BLOCK_GROUP = "block_group"
    FACILITY = "facility"
    NETWORK = "network"


@dataclass(frozen=True)
class Source:
    """A single dataset the pipeline can acquire."""

    key: str                      # stable identifier; cache subdirectory
    title: str
    provider: str
    grain: Grain
    role: str                     # what the model uses it for
    availability: Availability
    url: str = ""                 # primary endpoint or bulk file
    probe_url: str = ""           # representative request used by probe.py;
                                  # for APIs this must carry real query
                                  # parameters, or the probe only proves the
                                  # host is up rather than the data reachable
    docs_url: str = ""            # human landing page
    licence: str = "US Government Work (public domain)"
    key_env: str = ""             # environment variable holding the API key
    cadence: str = ""             # how often the publisher updates it
    lag_months: float | None = None   # reporting lag, for the currency figure
    notes: str = ""
    fields: tuple[str, ...] = field(default_factory=tuple)
    vintages: tuple[str, ...] = field(default_factory=tuple)
    handled_by: str = ""
    # Module that acquires this source, when a generic GET cannot. An API
    # endpoint needs a variable list and paging, and fetching the bare URL
    # returns the provider's metadata catalog - a file that looks like data,
    # is not, and would sit in data/raw/ looking plausible.
    # Years to fetch when the series is published one file per year. Empty
    # means a single current file. Declared here rather than in the fetch
    # loop so "which years does the panel cover" has one answer.

    @property
    def usable(self) -> bool:
        """True when the pipeline can acquire it without human action."""
        return self.availability is Availability.OPEN


# ---------------------------------------------------------------------------
# The registry. Order is the order the acquire stage runs them.
# ---------------------------------------------------------------------------
