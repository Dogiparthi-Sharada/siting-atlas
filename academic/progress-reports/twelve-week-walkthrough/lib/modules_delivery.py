"""Weeks 9-12: the cost model, the real depot layer, and the delivery.

See ``spec.py`` for the conventions these entries obey.
"""

from __future__ import annotations

from modmeta import INSPECT, RECOMPUTE, pct, usd

WEEKS = [
    dict(
        n=9, title="What it costs to put a parcel on a doorstep",
        mode=RECOMPUTE,
        question="Forget prediction. Can free public data price the "
                 "operation itself?",
        artefacts=["cost_report"],
        secs=52,
        runs="make cost — recomputes all five scenarios offline",
        body="""
A Daganzo continuous approximation. Distance per stop is

    d = (k / sqrt(density)) * rho  +  2L / C

— a local term that falls as one over the square root of stop density, plus
a line haul amortised over the tour. Road geometry, wages and population
density, with no operator disclosure of any kind.

This is the week where the answer is yes. It is also the week to be clear
about what "works" means: the method is published, every parameter is
sourced or explicitly flagged as unsourced, and the result survives five
stress scenarios. It has **not** been validated against the operator's
realised costs, because nobody publishes those.

This version still places depots by a p-median solve. Week 10 removes that
assumption.
""",
        nums=lambda L: [
            ("ZCTAs costed", f"{L('cost_report')['baseline']['zctas']:,}",
             "cost_report.baseline.zctas"),
            ("Median cost per parcel",
             usd(L("cost_report")["baseline"]["median_cost_per_parcel"]),
             "cost_report.baseline.median_cost_per_parcel"),
            ("p10 / p90",
             f"{usd(L('cost_report')['baseline']['p10'], 2)} / "
             f"{usd(L('cost_report')['baseline']['p90'], 2)}",
             "cost_report.baseline.p10, p90"),
            ("Scenarios", len([k for k in L("cost_report")
                               if isinstance(L("cost_report")[k], dict)]),
             "cost_report top-level scenario keys"),
        ],
        limits=[
            "SUPERSEDED by week 10. This run places 334 depots by a p-median "
            "solve — buildings the operator never chose. It is kept here "
            "because the before/after is itself the result.",
            "Not validated against realised costs. No operator publishes "
            "them, so the model is checkable but not verified.",
        ],
        nxt=[("docs/ALGORITHMS.md", "the Daganzo approximation and its "
              "regime of validity")],
    ),
    dict(
        n=10, title="Replacing the model's depots with real buildings",
        mode=RECOMPUTE,
        question="What changes when the depot layer stops being a solve and "
                 "becomes the buildings the operator actually runs?",
        artefacts=["cost_by_station"],
        secs=17,
        runs="python -m siting_atlas.cost.station_runner — every "
             "scenario, offline",
        body="""
Week 9's p-median is a good solve of the wrong problem. Once the facility
panel carries geocoded delivery stations, the assumption can be DELETED
rather than improved: depots are those buildings, there is no placement
step, and no capacity story to apologise for.

The headline moves the "wrong" way, and that is the finding. A p-median
minimises demand-weighted distance by construction; real siting is
constrained by land, labour, zoning and lease terms. The gap between the
two is what the increase measures.

Only address-geocoded stations are used. The rest carry a ZCTA-centroid
fallback, and a centroid is not a building — using one would put a depot in
the middle of its own catchment and drive that line haul to roughly zero,
which is the single most cost-reducing error available in this model.
""",
        nums=lambda L: [
            ("Stations used",
             L("cost_by_station")["stations"]["geocoded_used"],
             "cost_by_station.stations.geocoded_used"),
            ("Excluded as centroid fallbacks",
             L("cost_by_station")["stations"][
                 "excluded_zcta_centroid_fallback"],
             "...stations.excluded_zcta_centroid_fallback"),
            ("ZCTAs costed",
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
            ("Change against week 9",
             "{:+.2%}".format(
                 L("cost_by_station")["scenarios"]["baseline"][
                     "median_cost_per_parcel"]
                 / L("cost_report")["baseline"]["median_cost_per_parcel"]
                 - 1),
             "the two artefacts, divided"),
        ],
        limits=[
            "Coverage is now decided by where the operator built, not by a "
            "chosen study area. A ZCTA more than 15 miles from any station "
            "is left uncosted rather than costed badly.",
            "Twenty stations have no ZCTA inside the catchment and "
            "contribute to no cost, so the map draws more stations than "
            "the cost tables price.",
        ],
        nxt=[("docs/NUMBERS.md", "the full before/after, section 10.3")],
    ),
    dict(
        n=11, title="Five programmes that were retired", mode=INSPECT,
        question="What was built, run, and then taken out — and why is it "
                 "still in the repository?",
        artefacts=[],
        why_inspect=(
            "there is nothing to recompute — the archive is a directory, "
            "and it is read at build time"),
        runs="lists experiments/ and its notes",
        body="""
A survival model, a gravity formulation of network pull, two covariate
transforms and a portfolio optimiser. Each was built, run, and retired.
Their code, artefacts and notes are archived rather than deleted, and
nothing in `src/` imports any of them.

Keeping them is a deliberate choice about what a research artefact is for.
A repository that shows only what worked teaches the reader nothing about
the search, and invites them to repeat it. The archive records what each
programme asked and what came back.

Worth defending directly: retiring a programme is not the same as it having
been a mistake. The survival model was the right thing to try given what
was known at the time, and knowing it does not work here IS a result.

The table below counts **seven directories, not seven programmes**. Five
are the retired programmes above; `retired-tests` holds the tests that
retired with them, and `superseded-artefacts` holds outputs a later run
replaced — kept so a number quoted in an older document can still be
traced to the artefact it came from.
""",
        nums=lambda L: [],
        dirs="experiments",
        limits=[
            "Retired code is not maintained and is not covered by the test "
            "suite. It is evidence of a search, not a working component.",
        ],
        nxt=[("experiments/README.md", "what each programme asked and what "
              "came back"),
             ("docs/DECISION_LOG.md", "when each was retired, and on what "
              "evidence")],
    ),
    dict(
        n=12, title="The artefact itself", mode=RECOMPUTE,
        question="Can a stranger clone this, run it, and get the same "
                 "numbers — and can they tell when they have not?",
        artefacts=["scope", "viz_report"],
        secs=463,
        measured_note="694 tests passed, 2 xfailed, then the full offline "
                      "reproduction",
        runs="make test && make reproduce",
        body="""
The deliverable is not the finding, it is the thing that lets someone check
the finding. Offline reproduction from a clone, no API keys; a test suite;
a pre-registration seal verified in CI; figures that read their numbers
from artefacts rather than carrying typed-in values; and an IEEE-format
write-up.

That last rule has a history. This project shipped a figure with nine
hand-entered values and a fabricated confidence band. It found it in its
own audit, fixed it, and the remedy was not "be more careful" but "make it
impossible" — a figure now either reads from an artefact or carries no
numbers at all. The same rule generates the twelve pages you are reading.

**The honest close.** Three of the project's four original claims are still
ambitions; only the artefact claim and the explainability-ceiling claim are
evidenced. Saying so is the point.
""",
        nums=lambda L: [
            ("Panel shipped", f"{L('scope')['panel']['rows_label']} rows, "
             f"{L('scope')['panel']['megabytes']} MB",
             "scope.panel"),
            ("Reproduction", "offline, no API keys", "Makefile: reproduce"),
        ],
        limits=[
            "Matplotlib PNGs are not byte-reproducible — embedded timestamps "
            "and freetype version. Figure checks verify existence and "
            "provenance, not bytes. The .docx build IS byte-reproducible.",
            "Reproduction starts at L3. Re-deriving the panel itself is "
            "week 1-4 territory and needs ~4 GB plus three API keys.",
        ],
        nxt=[("docs/REPRODUCE.md", "the reproduction contract"),
             ("docs/STATUS.md", "the measured state of everything, with a "
              "run_id behind every number"),
             ("paper/", "the IEEE write-up")],
    ),
]
