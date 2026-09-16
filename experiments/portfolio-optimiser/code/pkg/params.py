"""Assumptions governing how activations interact and what they cost.

Separated from the objective for the same reason `cost/params.py` is: a
reviewer who wants to challenge a number should find every number in one
place, and a scenario sweep should be a list of frozen instances rather than
a mutated global. Source marks follow that module's convention: SOURCE,
ESTIMATE, DISAGREES. Ranges and measured sensitivities are in
docs/data/PARAMETERS.md sec. 4; the bibliography is docs/REFERENCES.md.

Read this before quoting a portfolio
------------------------------------
The cost ranking is robust and this is not. No cost parameter reordered the
2,333 ZCTAs by more than a Spearman rho of 0.90, but two of the five numbers
below reorder the PORTFOLIO almost completely: at `cannibalisation_peak` 0.35
only 38% of the funded ZIPs are the same ones, and at
`cannibalisation_radius_km` 10 only 54% are. Both are unsourced, and the peak
is the worse of the two - see its docstring.

The break-even margin is the wrong thing to look at when judging that, because
it moves only a few percent while the selection turns over. Report the overlap
as well as the margin, or the stability will look better than it is.

One number dominates all of them: the optimality gap of the heuristic itself
is 13.4%, which is larger than every parameter effect in the table. Improving
the solver buys more than re-estimating any of these constants.

Two things a 2026-09-13 literature pass established, both of which change how
the numbers above should be read
--------------------------------------------------------------------------
`capital_per_activation_usd` and `cannibalisation_peak` — the two parameters
that move the PORTFOLIO most — are not independent. They are one defect. The
objective prices `annual_parcels` and `annual_cost` as if an activation were a
ZCTA of resident demand, but prices CAPITAL and CANNIBALISATION as if it were
a facility with a catchment. Deciding what an activation IS fixes both at
once; tuning them separately cannot. See docs/data/PARAMETERS.md sec. 7.5.

And the $2bn budget does not bind and never did. Capacity is 500 activations;
greedy stops at ~282 on negative marginal NPV. Any sentence of the form "a
$2bn budget deploys $1.3bn" is already reporting a slack constraint.
"""

from __future__ import annotations

from dataclasses import dataclass

# Aliased on import: this module defines its own BASELINE (a
# PortfolioParameters), and two objects of different types under one name in
# one file is how someone eventually reads the wrong delivery calendar.
from ..cost.params import BASELINE as COST_BASELINE


@dataclass(frozen=True)
class PortfolioParameters:
    """Assumptions governing how activations interact and what they cost."""

    capital_per_activation_usd: float = 4_000_000.0
    """Midpoint of the $3-5M range used throughout the proposal.

    ESTIMATE, and the UNIT is more questionable than the number. `select.py`
    computes capacity as budget / this, `objective.py:164` charges
    `n_selected * this`, and there is NO de-duplication across ZCTAs that
    would share a station. The unit bought is a ZCTA, not a facility.

    How wrong, measured rather than guessed (2026-09-13). The tempting
    arithmetic is "median 58 ZIPs per station, so ~300 ZIPs is a few dozen
    stations, so the true capital is tens of millions". That is wrong by about
    twentyfold, because a delivery station has a THROUGHPUT and the funded
    ZCTAs are the densest ones. Per metro, taking max(15-mile disk cover,
    ceil(parcels / 40k)): the funded set needs ~103 stations, not ~6 and not
    the 282 charged. $412M against $1,128M — an overcharge of 2.7x, not 30x.

    The finding does NOT invert, for a reason worth writing down: the budget
    ALREADY does not bind. Capacity is 500 and greedy stops at 282 on negative
    marginal NPV. "Deploys $1.32bn of $2bn" is a statement that the budget is
    slack. Correcting the unit would make it vacuous rather than merely slack
    — the whole 11-metro pilot needs 334 depots, i.e. $1.336bn, so $2bn builds
    everything with $664M spare.

    What the literature does here, RE-READ 2026-09-13 and previously
    mis-summarised in this docstring. Neither paper "refuses" to price a
    facility. Holmes sets omega_0 = 0 (p. 260) for "the analysis of WHERE
    Wal-Mart places a GIVEN NUMBER of stores" and says of sunk cost (p. 262)
    "Implicitly, sunk costs are large ... This leaves the objective unchanged".
    HNS disregard sunk cost by exploiting timing "RATHER THAN the optimality of
    the NUMBER of facilities" and "provided these are the same across
    facilities" (p. 166), and state their estimator "is only able to capture
    costs that vary across the locations" (p. 178). Both are silent on the
    value, not hostile to the term, and both are silent for a reason that does
    not apply to us: we choose HOW MANY units to fund, which is exactly the
    margin they say they are not working on. KEEP A CAPITAL TERM; fix the unit.
    Holmes's $18M/year is a DC OPERATING cost, footnote 20 p. 287, four inputs
    and no source for any of them.

    $2M-$8M moves the break-even margin -7.6%/+13.5% and the portfolio from
    419 to 250 ZIPs, with only ~70% overlap at either end.

    See docs/research/NOTES_holmes_2011_capital_and_cannibalisation.md and
    NOTES_hns_2023_capital_and_cannibalisation.md for the quotes and pages,
    and docs/data/PARAMETERS.md sec. 6.16 for the full arithmetic. This and
    `cannibalisation_peak` are ONE defect, not two — see sec. 7.5 there.
    """

    horizon_years: int = 7
    """Convention. 5 years gives +5.5% on the break-even margin, 10 gives
    -4.3%. Both Econometrica ancestors write an infinite horizon and then
    arrange never to solve it."""

    discount_rate: float = 0.10
    """DISAGREES, defensibly. Holmes (2011) and Houde, Newberry and Seim
    (2023) both set beta = 0.95, about 5.3% a year, and neither cites a source
    for it. VERIFIED by opening both papers on 2026-09-13: Holmes p. 261, "the
    discount factor each period is beta. The period length is a year, and the
    discount factor is set to beta = .95"; HNS p. 165, in a subordinate clause
    under eq. (11), "where beta = 0.95 is Amazon's discount factor". Those are
    the complete treatments in both papers. Ours is 1.9x theirs, on the
    argument that theirs is nearer a social rate while this is a private hurdle
    rate for a logistics investment; Damodaran's industry cost-of-capital
    dataset puts trucking and transportation WACCs in the high single digits to
    low teens. Keep it, but state the disagreement. 5%-15% moves the break-even
    margin -3.3%/+3.2%."""

    cannibalisation_radius_km: float = 20.0
    """Distance beyond which two activations stop competing.

    Matches the donor-pool gate's default so the optimiser and the inferential
    safeguard cannot disagree about what "nearby" means — if they diverged,
    the agent would clear a write the optimiser had already priced.

    ESTIMATE. That consistency argument is a good reason for the two to AGREE
    and no reason at all for the value to be 20. Published comparators exist
    and all measure something else: Holmes (2011) caps a consumer's Wal-Mart
    choice set at 25 miles; Houde, Newberry and Seim (2023) cluster facilities
    within 20 miles and use MWPVL's 150-mile sortation catchment. 20 km is
    12.4 miles, below all of them.

    Small effect on the margin (-2.9%/+1.9% over 10-40 km) and the largest
    effect on the ANSWER anywhere in the project: at 10 km only 54% of the
    funded ZIPs are the same ones, and n moves 418 to 279.
    """

    cannibalisation_peak: float = 0.18
    """Maximum share of volume a ZCTA can lose to active neighbours.

    Applied through a SATURATING function of neighbour exposure,
    ``peak * (1 - exp(-exposure))``, not by summing over neighbours. The
    additive form was tried first and is wrong: exposure for a ZCTA in a
    densely selected metro reaches 90, so a linear rule claimed 500 nearby
    activations destroy 90% of each other's demand. That is arithmetic, not
    economics — a household that stops ordering because of one new facility
    cannot stop ordering again because of the next twenty. The ceiling is the
    behavioural quantity, so the ceiling is what gets parameterised.

    PLACEHOLDER: in the finished project this is the Pollmann distance-band
    estimate rather than a constant, so swapping it in changes one number.

    NOT a clean disagreement with a published number. Both Econometrica papers
    were re-read for this on 2026-09-13 and the previous summary here was wrong
    in three ways.

    1. The Holmes figure is 12.3%, not 10%. Table VIII p. 275: stand-alone
       $41.4M vs incremental $36.3M is (41.4-36.3)/41.4 = 12.32%. His prose
       rounds his own table. The food row, $44.8M vs $40.2M, IS 10.3%.
    2. We were comparing a CEILING to an AVERAGE. This parameter is a maximum;
       Holmes's "All" row averages over his whole 50-year diffusion including
       greenfield entry. His by-maturity rows, which we never quoted, run
       1.8% / 4.8% / 8.1% / 14.5% / 20.1% / 33.6% as a state fills up. The
       right comparator for a saturation ceiling is 33.6%. On that reading
       0.18 is CONSERVATIVE, and the 0.35 "stress test" is his measured value.
    3. Decisively: the quantity probably does not transfer at all. Holmes
       cannibalises sales at a store — a consumer picking one outlet from a
       25-mile choice set (p. 265). We reduce annual_parcels for a ZCTA, and
       those parcels are generated by the households RESIDENT in it. They do
       not order less because a neighbouring ZIP was activated; there is no
       second outlet to divert them to. HNS measure our quantity directly:
       their Table VIII (pp. 180-181) opens three San Bernardino FCs early,
       Arizona loses 88% of its orders, and the SYSTEM-WIDE change in orders
       under a tax-neutral counterfactual is EXACTLY ZERO. All of it is
       reallocation between facilities. They also tested whether household
       spending responds to facility proximity and could not reject
       independence (p. 165).

    So the prior caveat in this docstring — that we cannibalise volume which
    does not walk, so our peak should be LOWER — was right and understated. It
    is not an argument for 0.10 over 0.18; it is an argument that no non-zero
    value is well founded under the current specification.

    Measured 2026-09-13 (n, break-even, Jaccard vs the 0.18 selection):
        0.000 HNS-implied  313  $1.1788  0.574
        0.123 Holmes all   302  $1.2974  0.808
        0.180 CURRENT      282  $1.3431  1.000
        0.336 Holmes 21+   177  $1.3369  0.457
    Note the margin is NOT monotone — it peaks near 0.20 and falls by 0.336,
    because heavy cannibalisation drives the optimiser into a smaller, denser,
    individually cheaper portfolio. Judge this parameter on the overlap column.

    Report at 0.00, 0.18 and 0.336 side by side, not at 0.10 and 0.18. See
    docs/data/PARAMETERS.md sec. 7.4, and sec. 7.5 for why this and
    `capital_per_activation_usd` are the same defect.
    """

    linehaul_sharing: float = 0.35
    """Maximum share of line-haul cost avoided by sharing trips with
    neighbours. Saturating on the same exposure, for the same reason: a trip
    can only be shared away once.

    ESTIMATE, and it does not need to be better: zeroing it entirely moves the
    break-even margin 0.12%. That is the expected result and a good one —
    `objective.py` deliberately restricts the shareable pool to the
    mileage-driven share of cost, and mileage is ~11% of the bill. Worth
    building correctly; not worth defending.
    """

    delivery_days_per_year: float = COST_BASELINE.delivery_days_per_week * 52.0
    """Days a year the network actually delivers — 6 x 52 = 312, not 365.

    Derived from the cost model rather than typed, because the two must
    agree: ``daily_parcels`` and ``daily_cost_usd`` are per DELIVERY day, so
    annualising at 365 invents 53 days of volume that never happen. It
    matters more here than in cost/ because capital per activation is a fixed
    sum that does NOT scale with the flow — inflating parcels and operating
    cost together therefore shrinks capital's share and reports a break-even
    margin ~3.5% lower than the truth.
    """

    @property
    def annuity_factor(self) -> float:
        """Present value of $1/year for the horizon."""
        r, n = self.discount_rate, self.horizon_years
        return (1 - (1 + r) ** -n) / r



#: The configuration reported in the proposal. Scenarios derive from it with
#: ``dataclasses.replace(BASELINE, discount_rate=0.12)``.
BASELINE = PortfolioParameters()
