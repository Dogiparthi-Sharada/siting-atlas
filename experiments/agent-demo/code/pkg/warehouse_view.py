"""The WarehouseView Protocol, implemented against the real DuckDB file.

Why this is a separate module from gates.py
-------------------------------------------
``gates.py`` declares what a gate is allowed to SEE and deliberately does not
say where it comes from — that is the whole reason ``WarehouseView`` is a
Protocol. Keeping the concrete implementation here means the gate layer
still imports nothing from the warehouse layer, the stub in the tests is
still a valid view, and this file can grow a cache or an index without a
single gate changing.

The two things worth reading carefully below are the unit conversion in
:meth:`neighbours_within` and the donor-pool fallback. Both are places where
a plausible-looking implementation is quietly wrong.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

from ..common import paths
from ..common.db import connect
from ..common.logging_setup import get_logger
from ..cost.daganzo import haversine_miles
from ..models.truthy import as_boolean

_log = get_logger("agent.warehouse_view")

#: The Protocol speaks kilometres (gate 5's radius comes from an estimated
#: decay in km) and the project's distance function returns miles, because
#: the cost model is denominated in dollars per mile. Converting in one
#: named place beats converting at four call sites, one of which will be
#: forgotten: a 20 km radius read as 20 miles searches 2.6x the area and
#: quietly widens the contamination check, while the reverse silently
#: narrows it and lets a contaminated donor through.
KM_PER_MILE = 1.609344

#: What the geography methods see when there is no warehouse to read. Shaped
#: like the real query result so every caller downstream takes its ordinary
#: empty path instead of a special case.
_NO_CENTROIDS = pd.DataFrame({"zcta": pd.Series(dtype=object),
                              "latitude": pd.Series(dtype=float),
                              "longitude": pd.Series(dtype=float)})


class DuckDBWarehouseView:
    """Read-only view of warehouse state for the gate pipeline.

    Opens the database once per method rather than holding a connection,
    because a gate run is a handful of queries against a 34k-row dimension
    and the centroid table is cached in memory after the first touch. A
    long-lived handle would instead mean a read lock held across an
    operator's coffee break.
    """

    def __init__(self, db_path: Path | None = None,
                 *, donor_pool: set[str] | None = None,
                 audit_dir: Path | None = None):
        self.db_path = Path(db_path) if db_path else paths.WAREHOUSE
        self.audit_dir = Path(audit_dir) if audit_dir else paths.AUDIT
        self._explicit_donors = (set(donor_pool)
                                 if donor_pool is not None else None)
        self._centroids: pd.DataFrame | None = None
        self._donors: set[str] | None = None
        self.donor_pool_basis = "unresolved"
        #: Set when the warehouse turns out to be unreadable, and copied into
        #: the audit record. Without it the record would say only that zero
        #: ZCTAs were seen, which is indistinguishable from an empty
        #: warehouse that was read successfully.
        self.warehouse_error: str | None = None

    # -- geography ---------------------------------------------------------
    def _load_centroids(self) -> pd.DataFrame:
        """ZCTA centroids, loaded once and kept.

        33,791 rows of three columns is about 1 MB. Re-querying per gate
        call would turn a millisecond of numpy into a round trip per
        mutation, and the table does not change during a run.
        """
        if self._centroids is None:
            if not self.db_path.exists():
                raise FileNotFoundError(
                    f"{paths.rel(self.db_path)} is missing; run "
                    f"python -m siting_atlas.warehouse.schema first")
            with connect(self.db_path, read_only=True) as db:
                self._centroids = db.df(
                    "SELECT zcta, latitude, longitude FROM dim_zcta "
                    "WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
            _log.debug("cached %d ZCTA centroids", len(self._centroids))
        return self._centroids

    def _centroids_or_empty(self) -> pd.DataFrame:
        """Centroids, or an empty frame when the warehouse is not readable.

        Every Protocol method goes through this rather than through
        :meth:`_load_centroids` directly. ``Gate.check`` promises it "must
        not raise for ordinary failures", and an unbuilt warehouse is the
        most ordinary failure there is — on a fresh clone it is the DEFAULT
        state. Letting FileNotFoundError out of gate 2 took down the whole
        pipeline before ``write_audit_record`` ran, so the one artefact the
        safety argument depends on (a record of every attempted write,
        including the refused ones) was never written. Degrading to "I know
        of no ZCTAs" instead makes gate 2 return a clean REJECT, and the
        reason it rejected is recorded in ``describe()``.

        The actionable error is not lost: it is logged once, and
        :meth:`_load_centroids` still raises it for a direct caller who is
        not a gate.
        """
        try:
            return self._load_centroids()
        except FileNotFoundError as exc:
            if self.warehouse_error is None:
                # Once per view: a gate run touches this from several gates
                # and the same error four times reads like four faults.
                self.warehouse_error = str(exc)
                _log.error("warehouse unreadable, treating the ZCTA universe "
                           "as empty: %s", exc)
            return _NO_CENTROIDS

    def zcta_exists(self, zcta: str) -> bool:
        return bool((self._centroids_or_empty()["zcta"] == zcta).any())

    def neighbours_within(self, zcta: str, km: float) -> set[str]:
        """Every OTHER ZCTA whose centroid is within ``km`` kilometres.

        Centroid-to-centroid, not boundary-to-boundary. That is an
        approximation and it is the right one here: gate 5 asks whether a
        new facility's catchment plausibly overlaps a donor, and a catchment
        is a driving radius from a point, not a polygon adjacency. It does
        mean a physically enormous rural ZCTA is judged by its middle, which
        errs toward missing a distant donor in a sparse area — noted rather
        than hidden, and irrelevant in the dense metros the pilot covers.

        The query ZCTA is excluded from its own neighbourhood. Including it
        would double-count: gate 5 already tests ``is_donor(m.zcta)``
        separately, and the two findings mean different things — "this write
        treats a control unit" is a different problem from "this write
        contaminates a nearby control unit".
        """
        frame = self._centroids_or_empty()
        row = frame.loc[frame["zcta"] == zcta]
        if row.empty:
            # Gate 2 rejects unknown ZCTAs before gate 5 runs, but a gate
            # must never be the thing that raises: returning empty keeps a
            # direct caller honest without an exception escaping the
            # pipeline.
            _log.warning("zcta %s is not in dim_zcta; no neighbours", zcta)
            return set()

        miles = haversine_miles(
            float(row["latitude"].iloc[0]), float(row["longitude"].iloc[0]),
            frame["latitude"].to_numpy(), frame["longitude"].to_numpy())
        within = np.asarray(miles) * KM_PER_MILE <= km
        hits = set(frame.loc[within, "zcta"]) - {zcta}
        _log.debug("%d neighbour(s) within %.1f km of %s", len(hits), km,
                   zcta)
        return hits

    # -- donor pool --------------------------------------------------------
    def donor_pool(self) -> set[str]:
        """The untreated units a synthetic control would draw on.

        When an explicit pool is supplied it is used and nothing is guessed.
        When it is not, the pool is derived from the panel's outcome column
        — and TODAY that column is entirely NULL, because the facility panel
        has not arrived. There is then no way to know which ZCTAs are
        untreated, so every ZCTA in the universe is treated as a nominal
        donor.

        The consequence is deliberate and should not be "fixed": gate 5 will
        escalate essentially every mutation, because with no treatment
        history there is no evidence that any write is safe for the donor
        pool. A gate that passes when it has nothing to check is worse than
        useless, since it produces a green tick that means "not examined".
        Fail loud, fail safe, and say why in the audit record.
        """
        if self._donors is not None:
            return self._donors

        if self._explicit_donors is not None:
            self._donors = set(self._explicit_donors)
            self.donor_pool_basis = "explicit"
            _log.info("donor pool: %d ZCTA(s) supplied explicitly",
                      len(self._donors))
            return self._donors

        treated = self._treated_zctas()
        universe = set(self._centroids_or_empty()["zcta"])
        if treated is None:
            self._donors = universe
            self.donor_pool_basis = "undetermined-universe"
            _log.warning(
                "the panel's 'enabled' column is unpopulated, so the donor "
                "pool cannot be identified; treating all %d ZCTAs as nominal "
                "donors. Gate 5 will escalate any mutation — conservative by "
                "design, not a defect. Pass donor_pool=... to override.",
                len(universe))
        else:
            self._donors = universe - treated
            self.donor_pool_basis = "derived-from-panel"
            _log.info("donor pool: %d never-treated ZCTA(s) of %d",
                      len(self._donors), len(universe))
        return self._donors

    def _treated_zctas(self) -> set[str] | None:
        """ZCTAs observed as enabled, or None when the target is unusable.

        Parsed with ``models.truthy.as_boolean`` rather than
        ``.astype(bool)``. ``pd.Series(["false"]).astype(bool)`` is ``[True]``
        — every non-empty string is truthy — so a panel whose outcome
        round-tripped through a CSV as the text "false" would mark every ZCTA
        as treated, empty the donor pool, and leave gate 5 checking a
        contamination question against a pool of nobody. It is invisible
        today only because ``enabled`` is 100% NULL; it fires on the first
        real facilities file, which is the run where it matters most.

        ``as_boolean`` raises on a token it does not recognise. That is the
        right trade here: a loud failure at the top of a gate run costs ten
        minutes, and a donor pool that is quietly wrong invalidates every
        inference the gate was protecting.
        """
        if not paths.PANEL.exists():
            return None
        try:
            frame = pd.read_parquet(paths.PANEL, columns=["zcta", "enabled"])
        except (KeyError, ValueError):
            return None
        flagged = as_boolean(frame["enabled"], column="enabled")
        if not flagged.any():
            return None
        return set(frame.loc[flagged, "zcta"])

    def is_donor(self, zcta: str) -> bool:
        return zcta in self.donor_pool()

    # -- audit -------------------------------------------------------------
    def audit_log_writable(self) -> bool:
        """Can a record of this decision actually be written?

        Gate 4 refuses a write that could not be traced, so this has to test
        the filesystem rather than assume it. ``os.access`` alone is not
        enough — it consults permission bits and lies on a read-only mount
        and on some network filesystems — so the check ends by creating and
        removing a real file.
        """
        try:
            self.audit_dir.mkdir(parents=True, exist_ok=True)
            probe = self.audit_dir / ".write_probe"
            probe.write_text("probe", encoding="utf-8")
            probe.unlink()
            return True
        except OSError as exc:
            _log.error("audit directory %s is not writable: %s",
                       paths.rel(self.audit_dir), exc)
            return False

    def describe(self) -> dict:
        """Provenance of the state the gates were run against.

        Goes into the audit record verbatim. A decision is only reviewable
        if you can tell what the world looked like when it was taken.

        Nothing here guards on ``db_path.exists()`` any more. That guard was
        on ``zctas`` alone, so a missing warehouse still blew up on the very
        next line at ``donor_pool()`` — the record could not be written at
        all, which is the failure the guard was there to prevent. The state
        accessors degrade on their own now, and ``warehouse_error`` says
        which of "empty" and "unreadable" the zero ZCTAs means.
        """
        # Both read BEFORE the dict is built, because either can be the call
        # that discovers the warehouse is unreadable and sets the error.
        zctas = int(len(self._centroids_or_empty()))
        donors = len(self.donor_pool())
        return {
            "warehouse": paths.rel(self.db_path),
            "warehouse_exists": self.db_path.exists(),
            "zctas": zctas,
            "warehouse_error": self.warehouse_error,
            "donor_pool_size": donors,
            "donor_pool_basis": self.donor_pool_basis,
            "audit_dir": paths.rel(self.audit_dir),
            "audit_writable": bool(os.access(self.audit_dir, os.W_OK))
            if self.audit_dir.exists() else False,
        }
