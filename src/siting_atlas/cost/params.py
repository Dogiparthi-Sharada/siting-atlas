"""Every assumption the cost model makes, in one auditable place.

A cost-to-serve figure is only as defensible as its inputs. Burying "120 stops
per van" in a formula makes the output impossible to challenge, so every
constant lives here with its provenance and the direction it biases the
answer. A reviewer who disagrees changes one number and re-runs. Nothing here
is fitted: these are engineering and operating assumptions, and the
*estimated* quantities come from the panel (wages, fuel, density).

Provenance
----------
Each field is marked SOURCE (a citation, with the claim named), ESTIMATE (no
published source found) or DISAGREES (a published figure exists and we do not
match it). Never upgrade an ESTIMATE without reading the source: a fabricated
citation is worse than an admitted guess. Ranges, measured sensitivities and
the four disagreements are in docs/data/PARAMETERS.md; the bibliography is
docs/REFERENCES.md. The finding that should redirect a reviewer's scepticism
is that the routing mathematics this module is named after is DECORATION (the
BHH constant moves the median 1.9% when wrong by half) while the unsourced
labour and consolidation assumptions carry the headline.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CostParameters:
    """Operating assumptions for one delivery configuration.

    Frozen so a scenario cannot be mutated halfway through a run: a sensitivity
    sweep constructs new instances with ``replace``, leaving each result
    traceable to the exact parameter set that produced it.
    """

    # -- tour geometry ---------------------------------------------------
    bhh_constant: float = 0.57
    """Beardwood-Halton-Hammersley constant in L ~ k*sqrt(n*A).

    0.57 is Daganzo's value for strip/ring-radial routing in a served zone.
    The asymptotic uniform-random TSP value is ~0.71; real routing beats
    random because drivers follow streets in sweeps. Using 0.57 is therefore
    the *optimistic* end, which biases cost DOWN - stated because it makes
    marginal ZCTAs look better than they are.

    SOURCE: Daganzo (1984), Transportation Science 18(3) 231-253 and 18(4)
    331-350, on Beardwood, Halton and Hammersley (1959); Larson and Odoni,
    Urban Operations Research (1981) sec. 6.4.8 restates it. This is the only
    constant here that arrived with a citation, which invites attack - and
    being wrong by half moves the median 1.9%, because local travel is 3.3% of
    the bill. Point a reviewer at service time instead."""

    stops_per_tour: int = 120
    """Deliveries per van per shift.

    ESTIMATE. The "industry figures run 100-150" this docstring used to
    assert could not be traced to anything citable; searching returns job
    adverts. What is true is weaker: at 9 hours and 2.4 minutes a door, 120
    stops fills 4.8 hours at doors and leaves 4.2 for driving - a consistency
    check between two unsourced numbers, not evidence. More stops spreads the
    lease and line haul thinner, so a higher true figure biases cost UP.
    90-180 moves the median ~+/-10%."""

    circuity: float = 1.30
    """Street distance / straight-line distance.

    SOURCE, a derivation rather than a citation: on a rectangular grid the van
    travels L1 while the crow flies L2, and averaging over a uniformly random
    direction gives exactly 4/pi = 1.2732. 1.30 is that plus 2% for non-grid
    detours; using 4/pi exactly moves the median -0.24%. Both published
    ancestors, Holmes (2011) and Houde, Newberry and Seim (2023), apply NO
    circuity, so this is the conservative choice. Do NOT cite Boeing's
    street-network circuity in support - that is edge-level circuity, a
    different quantity much closer to 1.0."""

    # -- vehicle ---------------------------------------------------------
    van_mpg: float = 14.0
    """Diesel sprinter-class van, loaded, stop-start duty cycle.

    ESTIMATE. EPA and manufacturer figures are unloaded highway-cycle numbers,
    a different duty cycle; NREL/TP-5400-70943 measures the right one and has
    not been read. 10-20 mpg moves the median under 1%."""

    maintenance_usd_per_mile: float = 0.19
    """Wear per mile, on top of fuel.

    SOURCE, with a caveat bigger than the number: ATRI's annual Analysis of
    the Operational Costs of Trucking puts repair and maintenance in the
    high-teens cents per mile - measured on CLASS 8 TRACTOR-TRAILERS, not
    vans. Almost certainly too high for a Sprinter, conservatively so, and
    worth 0.7% of the median, so it stays."""

    van_lease_usd_per_day: float = 41.0
    """Daily cost of the vehicle, paid whether or not it is full.

    ESTIMATE, and the largest unhedged exposure here. Commercial fleet lease
    rates are negotiated and unpublished; consumer adverts are the wrong
    market. $41 x 312 = $12,792/year reconstructs a $50-60k van over four to
    five years with insurance - a reconstruction, not a source. Charged as
    lease/stops_per_tour, so it is a flat $0.34 per stop everywhere: 22.8% of
    the pilot's bill, third-largest lever at -8.8%/+15.9% over $25-70."""

    avg_speed_mph: float = 22.0
    """Door-to-door average including stops in traffic, not posted limits.

    ESTIMATE. The comparators measure something else - ATRI's ~36 mph
    rush-hour truck speeds are a corridor, not a residential round. 15-30 mph
    moves the median +3.5%/-2.0%, far less than the +14.5% the old
    single-centroid model showed: realistic line hauls left less driving for a
    low speed to punish."""

    # -- labour ----------------------------------------------------------
    service_minutes_per_stop: float = 2.4
    """Park, walk, hand off, scan. The dominant time cost at high density.

    ESTIMATE, and the most serious evidence gap in the project: 66.5% of cost
    per stop rests on a number with nothing behind it. 1.5-4.0 minutes moves
    the median -25.0%/+44.3%, and note the asymmetry - if plausible values are
    symmetric the expected error runs upward, so $1.09 is likelier too low
    than too high. Places to look, none read, NONE currently supporting 2.4:
    the TU Delft work on last-mile vehicle stop time; the Urban Freight Lab
    parcel-locker field study; USPS OIG DR-AR-11-002; METRANS MF 5.1d."""

    shift_hours: float = 9.0
    """Hours in a delivery shift. DISAGREES - see labour_usd_per_hour, where
    this and delivery_days_per_week form an hours-per-year denominator that
    does not match the BLS convention for the wage it divides."""

    wage_loading: float = 1.32
    """Employer cost / base wage: payroll tax, benefits, workers' comp.

    DISAGREES. BLS's Employer Costs for Employee Compensation puts benefits
    near 30% of total compensation in private industry, implying a loading
    nearer 1.42; transportation and material-moving occupations sit higher
    still. 1.42 raises the median 5.6%. Left at 1.32 pending verification of
    the ECEC figure and flagged in docs/data/PARAMETERS.md sec. 7.2 rather
    than quietly changed. In the other direction: neither Holmes (2011) nor
    Houde, Newberry and Seim (2023) applies ANY loading, and Holmes calls his
    own gross-payroll approach crude."""

    # -- demand ----------------------------------------------------------
    parcels_per_household_per_week: float = 3.2
    """US residential average across all carriers.

    Anchored to published national volume rather than guessed: ~22 billion
    US parcels in 2023 over ~131 million households is 3.2 per household per
    week. Scaled by income in the demand model.

    SOURCE: volume from Pitney Bowes' Parcel Shipping Index, households from
    the Census Bureau; neither re-verified from its release, so pin both.
    Cross-checked against the literature, which no other demand parameter here
    can claim: Houde, Newberry and Seim (2023) report ~32 Amazon orders per
    household in 2016 - 0.62 a week - when Amazon held ~31% of US online
    retail, so ~2 online orders a week in 2016 against our 3.2 for 2023 across
    all carriers. Consistent in magnitude and direction of travel.

    Barely moves the level (+1.6%/-1.3% over 2.5-4.0, since volume enters only
    through 1/sqrt(density)) and is one of three parameters that genuinely
    move the RANKING (Spearman 0.91).
    """

    parcels_per_stop: float = 1.4
    """Parcels handed over in a single visit.

    A parcel is NOT a stop, and conflating them is a real error rather than a
    rounding one: service time is paid once per door, so charging 2.4 minutes
    to every parcel overstates the labour cost of exactly those dense,
    high-volume ZCTAs the ranking is supposed to identify as cheap.

    ESTIMATE for the magnitude - the concept is right and the number is a
    guess. No published consolidation ratio was found; METRANS MF 5.1d counts
    real parcel arrivals at one large residential building and has not been
    read. This is the LARGEST lever in the model (1.0 raises the median 39.3%,
    2.0 cuts it 29.5%) because it divides cost per parcel directly, so its
    elasticity is exactly -1 and it is invisible to the ranking. Consolidation
    has risen with order batching, so if 1.4 is stale it is stale LOW, biasing
    cost UP."""

    income_elasticity: float = 0.35
    """Parcel volume elasticity with respect to household income.

    Positive and well below 1: richer households order more, but far from
    proportionally. Set conservatively - a higher value would concentrate
    predicted demand in wealthy ZCTAs and flatter the ranking's top end.

    ESTIMATE, and the nearest published evidence argues LOWER. Houde, Newberry
    and Seim (2023, Table III) regress log relative spending on log income and
    get 0.226 with a standard error of 0.22 - indistinguishable from zero -
    and conclude log-income has no significant linear effect on spending.
    Their object is a spending ratio against offline, not a level elasticity,
    so it does not settle ours; it does mean 0.35 is not known. Nearly inert
    on the level (+0.4%/-0.8% over 0.0-0.7), which is why the conservative
    choice is cheap; rank effect 0.92, among the largest."""

    reference_income_usd: float = 75_000.0
    """Income at which the per-household parcel rate applies unscaled.

    A pivot, not a level: moving it rescales every ZCTA by a common factor and
    moves the median under 0.5%. Roughly the 2023 US median household income,
    which is the sensible place to pivot."""

    delivery_days_per_week: float = 6.0
    """Days a week the NETWORK delivers. Correct when dividing weekly volume
    into daily volume; used INCORRECTLY in labour_usd_per_hour below."""

    # -- line haul -------------------------------------------------------
    default_linehaul_miles: float = 25.0
    """Fallback depot-to-zone distance when geography cannot supply one.

    A guard, not a parameter: it moves the median by exactly 0.00% at every
    value tested, because every pilot ZCTA has a cbsa_code and a placed depot,
    so the fallback never fires. It starts mattering outside a CBSA."""

    parcels_per_depot_per_day: float = 40_000.0
    """Throughput of one delivery station, which sets how many a metro needs.

    This replaces a free "how far is the depot" assumption with a quantity
    that can be checked against the world. At 40,000 the pilot's 13.2M daily
    parcels imply ~329 depots; Amazon alone runs ~700-900 US delivery
    stations and the pilot holds 17.6% of US population, so all operators
    together should land near 250-320. The implied network is the right size.

    Typical published figures for a delivery station run 20,000-60,000
    packages a day, so this sits mid-range. Raising it builds fewer, more
    distant depots and pushes cost UP; lowering it does the reverse.

    SOURCE is the consequence test above, not a paper, and for a throughput
    that is the right kind of evidence: a badly wrong value could not produce
    a network the right size. The 700-900 station count is MWPVL
    International's, unverified here - though MWPVL is also the
    facility-network source Houde, Newberry and Seim (2023) rely on.

    Level-robust, rank-fragile: -2.5%/+1.7% on the median over 20k-60k, but
    the LARGEST rank mover in the model (Spearman 0.90), because it decides
    how many depots a metro gets and so which ZCTAs are near one.
    """

    def summary(self) -> dict:
        """Flat dict for logging and for the run's metrics record."""
        return asdict(self)

    def labour_usd_per_hour(self, annual_wage: float) -> float:
        """Fully-loaded hourly cost from a BLS annual mean wage.

        DISAGREES WITH THE SOURCE OF ITS OWN INPUT, and this is the largest
        known error in the model. The denominator is 9 x 6 x 52 = 2,808 hours,
        which conflates two quantities: how many days a week the NETWORK
        delivers, and how many hours a year one DRIVER works. A six-day
        network does not employ six-day drivers; it employs more drivers.

        BLS's Occupational Employment and Wage Statistics builds the annual
        mean wage this method consumes by multiplying the hourly mean by 2,080
        hours, so dividing it by 2,808 recovers an hourly rate ~26% BELOW the
        one BLS measured. Amazon's delivery-partner adverts describe four
        ten-hour days, i.e. 2,080.

        Measured: a 2,080 denominator moves the median $1.0875 -> $1.3704,
        +26.0%; with the wage_loading correction, +33.6%. Not applied because
        it changes the project's headline and that is the user's call - see
        docs/data/PARAMETERS.md sec. 7.1. The fix is an explicit
        driver_hours_per_year constant, NOT a tweak to delivery_days_per_week,
        which is needed at 6 for the volume side.
        """
        hours = self.shift_hours * self.delivery_days_per_week * 52.0
        return (annual_wage * self.wage_loading) / hours

    def fuel_usd_per_mile(self, diesel_usd_gal: float) -> float:
        return diesel_usd_gal / self.van_mpg

    def distance_usd_per_mile(self, diesel_usd_gal: float) -> float:
        """Marginal cost of a mile: fuel plus wear.

        Sanity check against the literature: this is ~$0.49, and adding paid
        driver time at 22 mph gives ~$1.61 a van-mile. Holmes (2011) was
        quoted $1.20 a truck-mile for in-house Wal-Mart trucking in 2005
        dollars - a tractor-trailer, and an older vintage. Same order of
        magnitude, and ours is the cheaper vehicle, which is the right sign.
        """
        return (self.fuel_usd_per_mile(diesel_usd_gal)
                + self.maintenance_usd_per_mile)


#: The configuration reported in the proposal. Scenarios derive from it with
#: ``dataclasses.replace(BASELINE, stops_per_tour=150)``.
BASELINE = CostParameters()

#: Bracketing scenarios for the sensitivity table. Each moves one lever a
#: plausible amount rather than an extreme, so the spread is a credible range
#: and not a worst case nobody believes.
SCENARIOS = {
    "baseline": BASELINE,
    "dense_routing": CostParameters(stops_per_tour=150,
                                    service_minutes_per_stop=2.0),
    "congested": CostParameters(avg_speed_mph=16.0, circuity=1.45),
    "high_fuel": CostParameters(van_mpg=11.0),
    "pessimistic_tour": CostParameters(bhh_constant=0.71),
}
