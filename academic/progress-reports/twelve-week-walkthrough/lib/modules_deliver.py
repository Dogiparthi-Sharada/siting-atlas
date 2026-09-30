"""Weeks 10-12: explain the failure, deliver what does work, ship it."""

from __future__ import annotations

from modmeta import INSPECT, RECOMPUTE, pct, usd

WEEKS = [
    dict(
        n=10, title="Diagnosis — why it failed, and what we retired",
        mode=INSPECT,
        question="Was the failure about our model, or about what free "
                 "public data can carry? And can you tell in advance?",
        artefacts=["covariate_search"],
        extra_json={"gravity": "experiments/gravity-network/artefacts/"
                               "gravity_network.json"},
        dirs="experiments",
        why_inspect=(
            "a live covariate refit is about ninety minutes on two "
            "workers; the archive listing is read at build time"),
        runs="reads the covariate search, the gravity arms, and the "
             "experiments archive",
        status="We can now say WHY, and turn it into a screening rule "
               "anyone can run before fitting. Five programmes were "
               "retired on the evidence and archived rather than deleted.",
        risk="Explaining a failure can slide into excusing it. The guard "
             "is that the rule is stated ONE-SIDED — it predicts failure, "
             "it does not promise success — and the band that would make "
             "it a two-sided rule is empty, which we show rather than "
             "assert.",
        body="""
A conditional choice model can only use a covariate that **varies inside a
metro**. Most free US public data is published at county grain, so across
two hundred candidate ZIP codes it arrives as a handful of distinct values.
A near-constant cannot rank anything, however large its real-world effect.

That gives a test you can run before fitting anything: measure each
covariate's within-metro coefficient of variation.

    cv below 0.6     it will fail          every one of them did
    cv 0.6 to 1.3    nothing lands here
    cv above 1.3     it may work           some did, some did not

The rule runs **one way**. Low dispersion is sufficient for failure; high
dispersion is necessary but nowhere near sufficient. Stating it as a
two-sided rule would be the overclaim, and the empty middle band is the
only reason the one-sided version is worth anything.

**What we retired.** A survival model, a gravity formulation of network
pull, two covariate transforms and a portfolio optimiser — each built, run,
and taken out on evidence. Their code and artefacts are archived, and
nothing in `src/` imports any of them. Retiring a programme is not the same
as it having been a mistake: the survival model was the right thing to try
given what was known in week 5, and knowing it does not work here is itself
a result.

The table below counts **directories, not programmes**. Five are the
retired programmes; `retired-tests` holds the tests that retired with them,
and `superseded-artefacts` holds outputs a later run replaced — kept so a
number quoted in an older document can still be traced to its source.
""",
        nums=lambda L: [
            ("Facilities in the search",
             L("covariate_search")["facilities"],
             "covariate_search.facilities"),
            ("Repeats", L("covariate_search")["repeats"],
             "covariate_search.repeats"),
            ("Terms screened",
             len(L("gravity")["terms"]["dispersion"][
                 "mean_within_metro_cv"]),
             "gravity_network...mean_within_metro_cv"),
            ("Below cv 0.6 — all failed",
             sum(1 for v in L("gravity")["terms"]["dispersion"][
                 "mean_within_metro_cv"].values() if v < 0.6),
             "derived from the same field"),
            ("Inside the band cv 0.6 to 1.3",
             sum(1 for v in L("gravity")["terms"]["dispersion"][
                 "mean_within_metro_cv"].values() if 0.6 <= v <= 1.3),
             "derived from the same field"),
        ],
        limits=[
            "Descriptive. Twenty-one non-independent terms from one run — "
            "a rule of thumb worth checking on your own data, not an "
            "estimated threshold with a confidence interval.",
            "The empty band is an observation about THESE covariates. It "
            "is not a claim that no covariate can sit at cv 1.0.",
            "Retired code is unmaintained and outside the test suite. It "
            "is evidence of a search, not a working component.",
        ],
        nxt=[("docs/EXPERIMENTS.md",
              "all 21 experiments and what each does NOT support"),
             ("experiments/README.md",
              "what each retired programme asked, and what came back"),
             ("docs/DECISION_LOG.md",
              "when each was retired, and on what evidence")],
    ),
    dict(
        n=11, title="What does work — pricing the operation",
        mode=RECOMPUTE,
        question="Forget prediction. Can free public data price the "
                 "operation itself — and what happens when we stop "
                 "inventing where the depots are?",
        artefacts=["cost_report", "cost_by_station"],
        secs=49,
        runs="make cost, then "
             "python -m siting_atlas.cost.station_runner",
        status="$1.14 to put a parcel on a doorstep, across 8,037 ZIP-code "
               "areas and 57.8% of US households — priced against 501 "
               "real buildings, from road geometry and wages alone.",
        risk="We shipped a first version that placed depots by a p-median "
             "solve, then realised the depot layer was an ASSUMPTION we "
             "had been treating as a parameter. Finding your own "
             "unclassified assumption late is the risk; the response was "
             "to delete it rather than tune it.",
        body="""
A Daganzo continuous approximation. Distance per stop is

    d = (k / sqrt(density)) * rho  +  2L / C

— a local term falling as one over the square root of stop density, plus a
line haul amortised over the tour. Road geometry, wages and population
density. No operator disclosure of any kind.

**The correction, which is the actual result of this week.** Version one
placed 334 depots by a p-median solve — buildings the operator never chose.
A p-median minimises demand-weighted distance *by construction*, so it was
quietly answering "what would this cost if sited optimally". Once the
facility panel carried geocoded stations, the assumption could be deleted
rather than improved: depots are those buildings, and there is no placement
step left to defend.

The headline moved the "wrong" way, and that is the point. The gap between
an optimal siting and a real one is what the increase measures.

Only address-geocoded stations are used. The rest carry a ZCTA-centroid
fallback, and a centroid is not a building — using one puts a depot in the
middle of its own catchment and drives that line haul to roughly zero,
which is the single most cost-reducing error available here.

**What "works" means.** The method is published, every parameter is sourced
or explicitly flagged as unsourced, and the result survives five stress
scenarios. It has **not** been validated against realised costs, because
nobody publishes those. Checkable, not verified.
""",
        nums=lambda L: [
            ("Pilot ZCTAs (p-median depots)",
             f"{L('cost_report')['baseline']['zctas']:,}",
             "cost_report.baseline.zctas"),
            ("Pilot median",
             usd(L("cost_report")["baseline"]["median_cost_per_parcel"]),
             "cost_report.baseline.median_cost_per_parcel"),
            ("Real stations used",
             L("cost_by_station")["stations"]["geocoded_used"],
             "cost_by_station.stations.geocoded_used"),
            ("ZCTAs costed against them",
             f"{L('cost_by_station')['coverage']['costed_zctas']:,}",
             "cost_by_station.coverage.costed_zctas"),
            ("US households covered",
             pct(L("cost_by_station")["coverage"][
                 "costed_household_share"]),
             "cost_by_station.coverage.costed_household_share"),
            ("Median cost per parcel",
             usd(L("cost_by_station")["scenarios"]["baseline"][
                 "median_cost_per_parcel"]),
             "cost_by_station.scenarios.baseline.median_cost_per_parcel"),
            ("Median line haul",
             f"{L('cost_by_station')['scenarios']['baseline']
                 ['median_linehaul_miles']:.2f} mi",
             "...scenarios.baseline.median_linehaul_miles"),
            ("Effect of using real buildings",
             "{:+.2%}".format(
                 L("cost_by_station")["scenarios"]["baseline"][
                     "median_cost_per_parcel"]
                 / L("cost_report")["baseline"]["median_cost_per_parcel"]
                 - 1),
             "the two artefacts, divided"),
        ],
        limits=[
            "Not validated against realised costs. No operator publishes "
            "them, so this is checkable but not verified.",
            "Coverage is decided by where the operator built, not by a "
            "chosen study area. A ZCTA more than 15 miles from any station "
            "is left uncosted rather than costed badly.",
            "Twenty stations have no ZCTA inside the catchment and "
            "contribute to no cost, so the map draws more stations than "
            "the cost tables price.",
        ],
        nxt=[("docs/ALGORITHMS.md",
              "the Daganzo approximation and its regime of validity"),
             ("docs/NUMBERS.md", "the full before and after, section 10.3")],
    ),
    dict(
        n=12, title="The artefact — and the defence", mode=RECOMPUTE,
        question="Can a stranger clone this, run it, and get the same "
                 "numbers — and can they tell when they have not?",
        artefacts=["scope", "viz_report"],
        secs=404,
        measured_note="694 tests passed, 2 xfailed, then the full offline "
                      "reproduction",
        runs="make test && make reproduce",
        status="694 tests, an offline reproduction from a clone with no API "
               "keys, a CI-verified pre-registration seal, and an "
               "IEEE-format write-up drafted.",
        risk="A result nobody can re-run is not a result. The specific "
             "risk we had to fix: this project once shipped a figure with "
             "nine hand-entered values and a fabricated confidence band. "
             "We caught it in our own audit — and the remedy was not 'be "
             "more careful' but 'make it impossible'.",
        body="""
The deliverable is not the finding. It is the thing that lets someone else
check the finding.

Offline reproduction from a clone with no API keys. A test suite. A
pre-registration seal re-verified in CI on every push. Figures that read
their numbers from artefacts rather than carrying typed-in values. An
IEEE-format paper.

That figure rule has a history, and it is the most useful thing to say in a
defence. An audit of our own work found a figure with nine hand-entered
values under a band labelled "95% CI", for a regression that had never been
run. The fix was structural: a figure now either reads from an artefact or
carries no numbers at all. **These twelve pages are generated by the same
rule** — every number above was pulled from a file at build time.

**How to close.** Three of the project's four original claims are still
ambitions. Only the artefact claim and the explainability-ceiling claim are
evidenced, and the right-hand column of the claims table says so. A
capstone that says "three of our four claims are unproven, here is exactly
which and why" is stronger than one that claims four out of four, because
the first can be checked.
""",
        nums=lambda L: [
            ("Panel shipped",
             f"{L('scope')['panel']['rows_label']} rows, "
             f"{L('scope')['panel']['megabytes']} MB",
             "scope.panel"),
            ("Reproduction", "offline, no API keys", "Makefile: reproduce"),
            ("Figures rebuilt from artefacts",
             len(L("viz_report")) - 2, "viz_report top-level keys"),
        ],
        limits=[
            "Matplotlib PNGs are not byte-reproducible — embedded "
            "timestamps and freetype version. Figure checks verify "
            "existence and provenance, not bytes. The .docx build IS "
            "byte-reproducible.",
            "Reproduction starts at L3. Re-deriving the panel itself is "
            "weeks 3 to 5 territory and needs about 4 GB plus three API "
            "keys.",
        ],
        nxt=[("docs/REPRODUCE.md", "the reproduction contract"),
             ("docs/STATUS.md",
              "the measured state of everything, run_id per number"),
             ("paper/", "the IEEE write-up")],
    ),
]
