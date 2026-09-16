"""The pilot metros, keyed to stable CBSA codes.

Why this file exists at all
---------------------------
The proposal names metros the way people say them: "San Francisco Bay Area",
"Austin". Every data source labels them differently. Something has to join the
two, and two obvious shortcuts both fail silently.

**Shortcut 1: substring matching on the name.** On the real Zillow strings:

    "Austin"   also matches   "Austin, MN"        (pop. 26,000, Minnesota)
    "New York" also matches   "New Bern, NC", "Newport, OR", "Newberry, SC"
    "San ..."  also matches   "Sandusky, OH", "Santa Fe, NM", "Susanville, CA"

None of those raise. They enlarge the pilot sample with the wrong ZCTAs and
every downstream estimate is then computed on a population nobody chose.

**Shortcut 2: matching on the full CBSA title.** Titles are revised with every
OMB delineation. Between the 2020 titles Zillow still publishes and the 2023
delineation this project uses, six of eleven pilot titles changed:

    San Francisco-Oakland-Berkeley, CA     -> ...-Oakland-Fremont, CA
    New York-Newark-Jersey City, NY-NJ-PA  -> ... NY-NJ        (PA dropped)
    Chicago-Naperville-Elgin, IL-IN-WI     -> ... IL-IN        (WI dropped)
    Austin-Round Rock-Georgetown, TX       -> ...-San Marcos, TX
    Denver-Aurora-Lakewood, CO             -> ...-Centennial, CO
    Miami-Fort Lauderdale-Pompano Beach FL -> ...-West Palm Beach, FL

A title join would have dropped six of the ten pilot metros and reported
nothing. **CBSA codes are stable across delineations**, so the code is the key
and titles are only ever labels.

Membership does not come from the rent index
--------------------------------------------
Taking whichever ZCTAs appear in Zillow's index was measured against the
official delineation: it drops **35% of pilot-metro ZCTAs**, and the dropped
ones have a median population of 4,731 against 30,589 for those kept. Zillow
publishes a rent index only where there are enough listings, so that filter
silently selects for density — and low-density fringe ZCTAs are exactly where
a same-day expansion decision is contested. The dense ones are foregone
conclusions. Filtering there would be selecting the sample on a correlate of
the outcome, in a project whose whole subject is selection.

So membership comes from the OMB delineation, and rent is a feature with
honest missingness.

The Bay Area decision
---------------------
"San Francisco Bay Area" is not one CBSA. It is at least five: SF-Oakland-
Fremont (41860), San Jose-Sunnyvale-Santa Clara (41940), Santa Rosa-Petaluma
(42220), Vallejo (46700) and Napa (34900).

This model takes the first two, because a same-day delivery territory is a
contiguous drive-time envelope and those two form one continuous urbanised
area. Santa Rosa, Vallejo and Napa are separated from it by low density — the
variable the cost model is most sensitive to, since cost per drop scales with
1/sqrt(density) — so folding them in would blend two operating regimes under
one label. That is a judgement call, not a fact: add the three codes below to
take the full nine-county Bay Area, and nothing else changes.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .logging_setup import get_logger

_log = get_logger("metros")


@dataclass(frozen=True)
class Metro:
    """One pilot metro and the CBSA codes that constitute it.

    Frozen because this is reference data. If a definition changes, that is an
    edit to this file under version control — not a runtime mutation that
    leaves no trace of which definition produced a result.
    """

    slug: str
    label: str
    cbsa_codes: tuple[str, ...]
    heldout: bool = False

    @property
    def is_composite(self) -> bool:
        """True when the everyday name covers more than one CBSA."""
        return len(self.cbsa_codes) > 1

    def __str__(self) -> str:
        """Readable one-liner: label, CBSA count, and fit/held-out."""
        kind = "held out" if self.heldout else "fit"
        return (f"{self.label} ({len(self.cbsa_codes)} CBSA"
                f"{'s' if self.is_composite else ''}, {kind})")


# Codes verified against the 2023 OMB delineation on 2026-09-12. `validate()`
# re-checks them against whatever file is actually loaded, so a delineation
# change surfaces as a warning rather than as a silently shrunken sample.
PILOT: tuple[Metro, ...] = (
    Metro("bay_area", "San Francisco Bay Area", ("41860", "41940")),
    Metro("new_york", "New York", ("35620",)),
    Metro("chicago", "Chicago", ("16980",)),
    Metro("austin", "Austin", ("12420",)),
    Metro("seattle", "Seattle", ("42660",)),
    Metro("denver", "Denver", ("19740",)),
    Metro("miami", "Miami", ("33100",)),
    Metro("nashville", "Nashville", ("34980",)),
    # Held out entirely from fitting. Phoenix is a large, fast-growing Sun Belt
    # metro and Boise a small one, so together they test transfer across both
    # geography and scale rather than only across time.
    Metro("phoenix", "Phoenix", ("38060",), heldout=True),
    Metro("boise", "Boise", ("14260",), heldout=True),
)


class MetroRegistry:
    """Lookup and validation over the pilot metro definitions.

    A class rather than loose functions because the reverse index (CBSA code
    back to metro) is built once and reused, and because tests construct a
    registry over a fixture subset without touching module state.
    """

    def __init__(self, metros: Iterable[Metro] = PILOT):
        """Index the metros by slug, label and CBSA code.

        Raises on a duplicate slug, and on a CBSA claimed by two metros — the
        reverse lookup would otherwise silently pick whichever was declared
        last, quietly reassigning a county's ZCTAs to the wrong metro.
        """
        self.metros: tuple[Metro, ...] = tuple(metros)

        self._by_slug: dict[str, Metro] = {}
        self._by_label: dict[str, Metro] = {}
        self._by_code: dict[str, Metro] = {}

        for metro in self.metros:
            if metro.slug in self._by_slug:
                raise ValueError(f"duplicate metro slug {metro.slug!r}")
            self._by_slug[metro.slug] = metro
            self._by_label[metro.label.casefold()] = metro
            for code in metro.cbsa_codes:
                if code in self._by_code:
                    raise ValueError(
                        f"CBSA {code} claimed by both "
                        f"{self._by_code[code].slug!r} and {metro.slug!r}; a "
                        f"county cannot belong to two pilot metros")
                self._by_code[code] = metro

    # -- lookup ----------------------------------------------------------
    def __len__(self) -> int:
        """Number of metros, not of CBSA codes — a composite counts once."""
        return len(self.metros)

    def __iter__(self):
        """Iterate the metros in declaration order."""
        return iter(self.metros)

    def get(self, key: str) -> Metro:
        """Resolve a slug or an everyday label. Raises on an unknown key."""
        found = self._by_slug.get(key) or self._by_label.get(key.casefold())
        if found is None:
            raise KeyError(
                f"{key!r} is not a pilot metro. Known: "
                f"{', '.join(m.slug for m in self.metros)}")
        return found

    def for_code(self, cbsa_code: str) -> Metro | None:
        """Reverse lookup: which pilot metro owns this CBSA code, if any."""
        return self._by_code.get(str(cbsa_code).strip())

    def codes(self, *, heldout: bool | None = None) -> tuple[str, ...]:
        """Every CBSA code in the pilot, optionally filtered by hold-out.

        ``heldout=False`` gives the fitting sample, ``True`` the transfer
        test, ``None`` everything.
        """
        return tuple(
            code
            for metro in self.metros
            if heldout is None or metro.heldout is heldout
            for code in metro.cbsa_codes
        )

    @property
    def fit_codes(self) -> tuple[str, ...]:
        """CBSA codes the model may be fitted on."""
        return self.codes(heldout=False)

    @property
    def heldout_codes(self) -> tuple[str, ...]:
        """CBSA codes reserved for the geographic transfer test."""
        return self.codes(heldout=True)

    # -- validation ------------------------------------------------------
    def validate(self, delineation) -> dict:
        """Check every declared code against the loaded delineation.

        ``delineation`` is the ``cbsa_county`` frame, or any iterable of CBSA
        codes. A missing code means OMB retired or merged a CBSA; left
        unchecked that drops a metro from the sample in silence, which is the
        failure this module exists to prevent.
        """
        try:
            observed = set(delineation["cbsa_code"].astype(str))
        except TypeError:
            observed = {str(c) for c in delineation}

        missing = [c for c in self.codes() if c not in observed]
        present = [c for c in self.codes() if c in observed]

        if missing:
            _log.warning(
                "%d declared CBSA code(s) absent from the delineation — the "
                "pilot sample is smaller than intended: %s",
                len(missing), ", ".join(missing))
        else:
            _log.info("all %d pilot CBSA codes present in the delineation",
                      len(present))

        return {"declared": len(self.codes()), "present": present,
                "missing": missing, "ok": not missing}

    def counties(self, delineation, *, heldout: bool | None = None):
        """The county GEOIDs constituting the pilot, as a DataFrame.

        Adds ``metro_slug`` and ``metro_label`` so downstream joins carry the
        everyday name without re-deriving it.
        """
        wanted = set(self.codes(heldout=heldout))
        sub = delineation[delineation["cbsa_code"].astype(str).isin(wanted)]
        sub = sub.copy()
        sub["metro_slug"] = [self.for_code(c).slug
                             for c in sub["cbsa_code"].astype(str)]
        sub["metro_label"] = [self.for_code(c).label
                              for c in sub["cbsa_code"].astype(str)]
        return sub

    def summary(self) -> list[str]:
        """Human-readable lines for a log or a report header."""
        return [f"  {m.slug:10} {m}" for m in self.metros]


#: Module-level default. Import this rather than constructing a registry, so
#: every caller shares one definition of the pilot.
REGISTRY = MetroRegistry()
