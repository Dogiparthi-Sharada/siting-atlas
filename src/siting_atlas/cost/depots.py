"""Where the vans start from — a network of depots, not one point per metro.

Why this module had to exist
----------------------------
The first version of the cost model used ONE depot per metro, at the
population-weighted centroid, and claimed the choice barely mattered. It
does not: one line-haul mile is $0.018 per parcel, the single-depot network
implied hauls of 0.4 to 145.7 miles, and the ranking was mostly measuring
distance from a metro's centre of mass. See `daganzo.py:116`.

Why it is no longer k-means
---------------------------
The fix above was right and the implementation underneath it was not. Depots
were placed by k-means, which minimises SQUARED distance and therefore
converges on the weighted MEAN. The cost model bills line haul in
`daganzo.py:159` as ``2 * L / stops_per_tour``, which is LINEAR in distance,
and the minimiser of weighted linear distance is the weighted MEDIAN. We
optimised one objective and charged for a different one.

It is not a rounding difference. One metro, 60 parcels/day at mile 0 and 40
parcels/day at mile 50:

    weighted mean    (mile 20)   2,400 parcel-miles   <- k-means
    weighted median  (mile  0)   2,000 parcel-miles   <- p-median

20% of the term the model is most sensitive to, and the error is one-sided:
the mean is pulled towards low-density outlying demand, so k-means
systematically sites depots away from the volume. Across the pilot the
switch removes 9.3% of billed parcel-miles and moves the ZCTA ranking by
Spearman rho 0.888 — as much as the most rank-sensitive parameter in the
model moves it across its whole plausible range.

The formulation
---------------
This is now the p-median problem, Klose and Drexl (2004) section 4,
equations (1a)-(1e): choose p of a candidate set J to minimise
``sum_k sum_j w_k d_kj z_kj`` subject to each demand node k being assigned to
exactly one open site. Candidates are the ZCTA internal points, so a depot
always stands on a row of the panel rather than on invented coordinates in
an empty field. See `docs/research/NOTES_hakimi_1964.md` for how far
Hakimi's node-optimality theorem does and does not license that, and
`docs/research/NOTES_klose_drexl_2005.md` section 5.2 for what choosing the
p-median over the CAPACITATED model gives away.

The short version of the giving-up. Our depots have a throughput,
`params.parcels_per_depot_per_day`, so the textbook model is the capacitated
facility location problem (Klose and Drexl section 5.2, constraint (11):
``sum_k d_k z_kj <= s_j y_j``). We do not solve it. We impose capacity only
in the AGGREGATE, ``sum_j s_j y_j >= d(K)`` — their constraint (6), the one
that turns the UFLP into the aggregate capacity plant location problem (7) —
which with identical depots is exactly the depot-count rule below. So a
single depot can be assigned more than its throughput while a neighbour sits
idle; the line haul reported here is therefore a LOWER BOUND on that of a
capacity-feasible network, and the model understates cost where demand is
bunched. Solving it properly would also mean solving the assignment, which
for a fixed set of open depots is the NP-hard generalised assignment problem
(their equations (13a)-(13d)), and that would have to reach into
`daganzo.py`, which takes nearest-depot distance and nothing else.

How the depot count is chosen
-----------------------------
Not by assumption. A delivery station has a throughput, so the number of
stations a metro needs falls out of its parcel volume:

    K = ceil(metro daily parcels / DS_PARCELS_PER_DAY)

Across the pilot that yields 334 depots for 13.2M daily parcels. That is a
genuine external check rather than a free parameter: Amazon alone runs
roughly 700-900 US delivery stations, the pilot holds 17.6% of the US
population, so all operators together should land near 250-320. The implied
network is the right size, which it had no way of being if the throughput
figure were badly wrong.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common.logging_setup import get_logger
from .daganzo import haversine_miles

_log = get_logger("cost.depots")

#: Interchange sweeps before we give up. Measured on the pilot: every metro
#: converges in 1 to 4, so the cap never binds and every placement is a true
#: 1-opt local optimum. A guard, not a knob.
MAX_INTERCHANGE_PASSES = 12


def solve_pmedian(dist: np.ndarray, weights: np.ndarray,
                  p: int) -> np.ndarray:
    """Choose ``p`` of the candidate sites to minimise ``sum_k w_k d_k``.

    ``dist`` is a (demand x candidate) matrix of miles, ``weights`` the
    demand at each row. Returns the chosen column indices, sorted.

    The exact problem is NP-hard and the pilot's largest metro reaches here
    with n = 848 and p = 109 (893 before `pilot_slice` drops householdless
    rows), so an exact MIP is not on the table. The standard two phases:

      1. GREEDY ADD. Open the site that most reduces the objective, repeat
         p times. O(p * n^2).
      2. VERTEX SUBSTITUTION, i.e. Teitz and Bart interchange: for each open
         site find the closed site that best replaces it and apply the swap
         at once, sweeping until a whole pass makes no move. O(p * n^2) per
         sweep. Applying every improving swap rather than only the single
         best one per pass matters: with one swap per pass the largest metro
         (p = 109) was still improving when it hit the pass cap and came out
         3.5% above the bound below instead of 0.6%.

    What that buys, stated honestly. On termination the solution is a 1-OPT
    LOCAL OPTIMUM: no single swap improves it. That is a statement about the
    neighbourhood searched, not a ratio against the true optimum, and vertex
    substitution has no constant-factor bound on the metric p-median. It does
    stop short sometimes: over 150 enumerable instances it is exact on 139,
    mean gap 0.27%, worst 11.0%, and the worst cases are all small p, where
    the optimum is two swaps away with no downhill path to it. See
    `tests/unit/test_depots_pmedian.py`, which pins that census.

    On the pilot it lands within 0.89% of a valid LAGRANGEAN LOWER BOUND
    (relax the assignment constraint (1b), take the p most negative reduced
    costs, 400 subgradient steps); per metro 0.00% -- two proved optimal --
    to 2.6%. So true suboptimality is at most 0.89% of the line-haul
    objective, which is itself ~8% of cost. The k-means it replaces was 20%
    off on a two-point example.

    Deterministic by construction: no randomness, and every tie is broken by
    the lowest index via ``argmin``. Depot locations feed the published
    ranking, so this is a requirement rather than a nicety.
    """
    n = dist.shape[1]
    if p >= n:
        return np.arange(n)

    w = np.asarray(weights, dtype=float)
    # Phase 1 -- greedy add. `best` is the distance from each demand node to
    # the nearest site opened so far. Scored as "objective after opening j"
    # rather than "gain from opening j" so no infinity is ever multiplied:
    # on the first pass `best` is all-inf and a zero-demand row would give
    # 0 * inf = nan.
    best = np.full(dist.shape[0], np.inf)
    chosen: list[int] = []
    for _ in range(p):
        after = (w[:, None] * np.minimum(best[:, None], dist)).sum(axis=0)
        after[chosen] = np.inf
        j = int(np.argmin(after))
        chosen.append(j)
        best = np.minimum(best, dist[:, j])

    sites = sorted(chosen)
    rows = np.arange(dist.shape[0])

    # Phase 2 -- vertex substitution. Closing an open site r sends every node
    # assigned to r to its SECOND-nearest open site, which is why both are
    # tracked; without `second` each candidate swap would need its own
    # recomputed row minimum and the sweep would cost O(p * n^3).
    for _ in range(MAX_INTERCHANGE_PASSES):
        moved = False
        i = 0
        while i < len(sites):
            sub = dist[:, sites]
            order = np.argsort(sub, axis=1, kind="stable")
            assign = order[:, 0]
            near = sub[rows, assign]
            second = (sub[rows, order[:, 1]] if len(sites) > 1
                      else np.full(len(rows), np.inf))
            current = float((w * near).sum())

            closed = np.setdiff1d(np.arange(n), sites, assume_unique=True)
            # A node the closing site did not own keeps `near`; one it did
            # own falls back to `second`. Either way the incoming candidate
            # may beat that.
            fallback = np.where(assign == i, second, near)
            after = (w[:, None] * np.minimum(fallback[:, None],
                                             dist[:, closed])).sum(axis=0)
            k = int(np.argmin(after))
            # A strictly positive threshold: float noise can manufacture a
            # gain of 1e-13 for ever and only the pass cap would stop it.
            if current - after[k] > 1e-9 * max(current, 1.0):
                sites = sorted(set(sites) - {sites[i]} | {int(closed[k])})
                moved = True   # re-examine slot i, which is now a new site
            else:
                i += 1
        if not moved:
            break

    return np.array(sites)


class DepotNetwork:
    """Depot locations for each metro, and the distance from every ZCTA.

    A class because placement is expensive relative to querying it: the
    network is solved once and then asked for distances many times during a
    scenario sweep.
    """

    def __init__(self, parcels_per_depot: float = 40_000.0):
        self.parcels_per_depot = parcels_per_depot
        self.depots: pd.DataFrame | None = None

    def fit(self, frame: pd.DataFrame, parcels: pd.Series) -> DepotNetwork:
        """Place depots, metro by metro, by solving a p-median per metro.

        ``frame`` needs ``cbsa_code``, ``latitude`` and ``longitude``.
        ``parcels`` is daily parcels per row and is the demand weight, so
        depots land where the volume is rather than at the geometric middle
        of a lot of empty land.

        One p-median per metro rather than one nationally. That is an
        assumption, not a decomposition: it forbids a depot in metro A from
        serving a ZCTA in metro B. For CBSAs hundreds of miles apart it costs
        nothing, and it is what keeps the problem tractable.
        """
        rows = []
        work = frame[["cbsa_code", "latitude", "longitude"]].copy()
        work["parcels"] = np.asarray(parcels, dtype=float)
        # A row with no usable coordinate cannot be a candidate site and
        # cannot have its distance measured. Left in, it silently poisoned
        # the whole metro's placement with NaN.
        usable = (np.isfinite(work["latitude"])
                  & np.isfinite(work["longitude"])
                  & np.isfinite(work["parcels"]))
        dropped = int((~usable).sum())
        if dropped:
            _log.warning("%d row(s) have no usable coordinate or volume and "
                         "cannot host or claim a depot", dropped)
        work = work[usable]

        for code, grp in work.groupby("cbsa_code", dropna=True):
            total = grp["parcels"].sum()
            if total <= 0 or len(grp) == 0:
                continue
            k = int(max(1, min(len(grp),
                               np.ceil(total / self.parcels_per_depot))))
            lat = grp["latitude"].to_numpy(float)
            lon = grp["longitude"].to_numpy(float)

            # The SAME metric the model then bills against. Optimising a
            # projected-plane approximation while charging great-circle
            # miles was the smaller sibling of the mean-versus-median bug;
            # an n x n haversine on 848 rows costs milliseconds.
            dist = haversine_miles(lat[:, None], lon[:, None],
                                   lat[None, :], lon[None, :])
            sites = solve_pmedian(dist, grp["parcels"].to_numpy(float), k)

            for s in sites:
                rows.append({"cbsa_code": code, "depot_lat": lat[s],
                             "depot_lon": lon[s]})
            _log.debug("cbsa %s: %.0f parcels/day -> %d depot(s)",
                       code, total, len(sites))

        self.depots = pd.DataFrame(
            rows, columns=["cbsa_code", "depot_lat", "depot_lon"])
        _log.info("placed %d depots across %d metros (%.0f parcels/depot)",
                  len(self.depots),
                  (self.depots["cbsa_code"].nunique()
                   if len(self.depots) else 0),
                  self.parcels_per_depot)
        return self

    def distance_miles(self, frame: pd.DataFrame,
                       fallback: float = 25.0) -> pd.Series:
        """Straight-line miles from each ZCTA to its NEAREST depot.

        Nearest, not the metro's: that is the whole point of the change. A
        ZCTA on the edge of a metro is served by the station built near it,
        not by one an hour away.

        Nearest is also the p-median's own assignment rule — constraints
        (1b) and (1c) of Klose and Drexl, which put each demand node on the
        cheapest open site — so the distance reported here is the distance
        the placement above was optimised for. It is NOT capacity-feasible;
        see the module docstring.
        """
        if self.depots is None or self.depots.empty:
            return pd.Series(fallback, index=frame.index)

        out = pd.Series(np.nan, index=frame.index, dtype=float)
        for code, grp in frame.groupby("cbsa_code", dropna=True):
            dep = self.depots[self.depots["cbsa_code"] == code]
            if dep.empty:
                continue
            # (zctas x depots) distances, then the minimum per ZCTA. The
            # pilot's largest is 848 x 109; a national run wants a KD-tree.
            d = haversine_miles(
                grp["latitude"].to_numpy(float)[:, None],
                grp["longitude"].to_numpy(float)[:, None],
                dep["depot_lat"].to_numpy(float)[None, :],
                dep["depot_lon"].to_numpy(float)[None, :])
            out.loc[grp.index] = d.min(axis=1)
        return out.fillna(fallback)

    def summary(self) -> pd.DataFrame:
        """Depots per metro, for logging and for the report."""
        if self.depots is None:
            return pd.DataFrame()
        return (self.depots.groupby("cbsa_code").size()
                           .rename("depots").reset_index())
