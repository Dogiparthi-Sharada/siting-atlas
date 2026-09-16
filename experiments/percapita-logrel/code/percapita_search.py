"""Does dividing by the numeraire recover the signal collinearity hid?

    OMP_NUM_THREADS=1 PYTHONPATH=src .venv/bin/python \\
        -m siting_atlas.models.percapita_search

The question
------------
`COVARIATES_TRIED.md` section 1.2 diagnoses a family of count columns as
UNIDENTIFIED rather than uninformative: each correlates 0.4-1.0 with
`households` within a metro, `households` is the numeraire with its
coefficient pinned at 1.0, and the model therefore cannot separate "people
live here" from "people live here and therefore own cars". If that
diagnosis is right, dividing by `households` should free the column and
some of them should start predicting.

The transform demonstrably removes the collinearity — `percapita_frame`
measures that directly, before and after, and it is reported whatever the
lift does. The open question is whether the columns were MASKED or simply
EMPTY. Both answers are publishable; the second closes the question.

`warehousing_establishments` is tested as a rate for a second reason. It
is the whole model (+3.65 of 6.39 large-metro lift), and
`NOTES_LEAKAGE_DECISIVE.md` prices a circularity risk on it. A RATE is
harder to contaminate by one building than a COUNT is: one new warehouse
moves a count of six to seven, and moves a per-household rate by the same
absolute amount divided by ten thousand households. So the swap arm —
the rate INSTEAD of the count — is a leakage test as much as a
specification test.

What this costs, and it is not a footnote
-----------------------------------------
Every column added here is INTENSIVE and therefore breaks Train section
3.4's zone-merger invariance, which `MODEL_SPEC.md` section 1 names as the
reason `V = ln(beta'a)` was adopted at all. The full argument is in
`percapita_frame`'s docstring and in `NOTES_PERCAPITA.md` section 2. It is
a priced trade-off — `inv_median_home_value` and the network-proximity
covariates already pay it — and it is still a real one.

Measurement rules, inherited and not relaxed
--------------------------------------------
1  ONE FRAME, COLUMN SUBSETS. Every arm is a `columns_only` view of the
   SAME `ChoiceData` that `covariate_search`'s core stage builds, so the
   choice sets are identical and the baseline arm must reproduce
   `covariate_search.json` exactly, and `baseline_reproduction` in the
   artefact records whether it did.
2  STRATIFIED BY CHOICE-SET SIZE, thinness judged on DISTINCT decisions.
3  NO SEARCH. Every arm is a fixed, pre-declared column list. The honest
   nested search in `covariate_search` came out 0.1476 WORSE than the
   baseline, which is a measured result about overfitting the selection;
   adding eight more candidates to it would measure that result again
   and nothing else.
4  A percentile spread over re-splits is NOT a standard error.
"""

from __future__ import annotations

import argparse
import os

import pandas as pd

from ..common import paths
from ..common.log_json import write_json
from ..common.logging_setup import configure
from ..warehouse.national import load_national
from .choice import ATTRACTIONS, CBP_ATTRACTIONS
from .choice_runner import SEED, TEST_FRACTION
from .covariate_frame import (
    RECIPROCALS,
    STATIC_CANDIDATES,
    build_frame,
    load_panel,
    static_frame,
)
from .covariate_harness import REPEATS
from .covariate_report import print_report
from .percapita_arms import distinct_counts, run_serial, summarise
from .percapita_frame import (
    MODEL_SOURCES,
    SOURCES,
    add_ratios,
    correlation_table,
    frame_correlations,
    print_correlations,
    ratio_name,
)
from .percapita_report import check

EXPANDED = (paths.ROOT / "data" / "external" / "facility_panel"
            / "national_facilities_expanded.csv")

ARTEFACT = "percapita_search.json"
CHECKPOINT = "percapita_repeats.json"

BASE = (*ATTRACTIONS, *CBP_ATTRACTIONS)
NO_WAREHOUSING = ATTRACTIONS
WAREHOUSING = CBP_ATTRACTIONS[0]

#: Arm order, declared BEFORE the run and never re-ordered afterwards.
#: `percapita_arms.run_serial` is arm-major, so on a machine that stops
#: the run early this list decides which questions get answered. The two
#: reproduction arms come first because nothing else is readable until
#: they match; then the column the baseline was most HARMED by
#: (`employment`, -0.1722) and the column the model is made of
#: (`warehousing_establishments`); then the rest, in descending order of
#: how much their level version cost the baseline.
#:
#: Declaring the order in advance is what stops it becoming a result. An
#: order chosen after seeing the lifts would be a selection rule.
PRIORITY = ("employment", "warehousing_establishments", "owner_occupied",
            "in_labor_force", "annual_payroll", "establishments",
            "bachelors_degree", "renter_occupied")

SWAP = "{} INSTEAD of the count"


def arms() -> dict:
    """Every arm, fixed and declared before the run, in priority order."""
    spec = {"baseline": list(BASE), "no_warehousing": list(NO_WAREHOUSING)}
    spec[SWAP.format(ratio_name(WAREHOUSING))] = [
        *NO_WAREHOUSING, ratio_name(WAREHOUSING)]
    for src in PRIORITY:
        if src in MODEL_SOURCES:
            spec[f"+ {ratio_name(src)}"] = [*BASE, ratio_name(src)]
    missing = set(MODEL_SOURCES) - set(PRIORITY)
    if missing:
        raise ValueError(f"PRIORITY does not cover {sorted(missing)}")
    return spec


def _load() -> tuple:
    if not EXPANDED.exists():
        raise SystemExit(f"\n  {paths.rel(EXPANDED)} not found\n")
    cbp = paths.INTERIM / "cbp_detail.parquet"
    if not cbp.exists():
        raise FileNotFoundError(
            f"{paths.rel(cbp)} is missing; without it the baseline is three "
            "covariates and nothing here is comparable to the published "
            "number. Run python -m siting_atlas.ingest.cbp_detail")
    panel = load_panel(paths.PANEL, STATIC_CANDIDATES, ())
    return load_national(EXPANDED), panel, pd.read_parquet(cbp)


def build() -> tuple:
    """The core frame of `covariate_search`, plus the ratio columns.

    The static column list and the reciprocals are the core stage's, not
    this experiment's, even though nine of the thirteen static columns go
    unused here. `static_frame` drops any ZCTA missing ANY requested
    column, so a shorter list would build a LARGER frame with different
    choice sets, and the baseline arm would no longer be comparable to the
    published 6.3889. Paying for nine unused columns buys that comparison.
    """
    facilities, panel, cbp = _load()
    data, coverage = build_frame(facilities, panel, cbp, CBP_ATTRACTIONS,
                                 static=STATIC_CANDIDATES,
                                 reciprocals=RECIPROCALS)
    z = static_frame(panel, STATIC_CANDIDATES, RECIPROCALS)
    return add_ratios(data), coverage, data, z


def run(repeats: int = REPEATS, resume: bool = True,
        fit: bool = True) -> dict:
    data, coverage, levels, z = build()
    spec = arms()
    distinct = distinct_counts(data)
    corr = correlation_table(levels, SOURCES)
    print_correlations(corr)
    # Scratch, not metrics: this is resume state, not a result. An existing
    # file under outputs/metrics still resolves, so no in-flight search is
    # thrown away by the move. See paths.checkpoint.
    checkpoint = paths.checkpoint(CHECKPOINT)
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    if not resume and checkpoint.exists():
        checkpoint.unlink()
    raw, complete = run_serial(data, spec, repeats, checkpoint,
                               fit=fit)
    unfinished = [n for n in spec if n not in complete]
    if "baseline" not in complete:
        raise SystemExit("\n  the baseline arm is unfinished; nothing here "
                         "is interpretable until it is. Re-run to resume.\n")
    done = {n: spec[n] for n in complete}
    summary = summarise(raw, done, "baseline", distinct)
    print_report("PER-CAPITA: eight count columns divided by the numeraire",
                 summary, "baseline")
    print("\n  distinct decisions per stratum (not decision-evaluations): "
          + ", ".join(f"{k}={v}" for k, v in distinct.items()))
    if unfinished:
        print(f"\n  UNFINISHED, not reported: {', '.join(unfinished)}")
    report = {
        "seed": SEED, "repeats": repeats, "test_fraction": TEST_FRACTION,
        "n_test_decisions": raw[0]["n_test"],
        "coverage": coverage, "reference_arm": "baseline",
        "distinct_decisions": distinct,
        "arms_declared": list(spec),
        "arms_complete": list(complete),
        "arms_unfinished": unfinished,
        "arms_unfinished_note": (
            "arm-major order, declared in percapita_search.PRIORITY before "
            "the run. An arm is reported only at the FULL repeat count; a "
            "part-finished arm is dropped rather than summarised over fewer "
            "re-splits than the baseline it is paired against."),
        "collinearity": corr,
        "collinearity_zcta_frame": frame_correlations(z, SOURCES),
        "baseline_reproduction": check(summary),
        "arms": summary,
        "extensivity_note": (
            "every _per_hh column is INTENSIVE. Train section 3.4 Example 2, "
            "cited by MODEL_SPEC.md section 1 as the reason for the "
            "ln(beta'a) form, requires attractions to ADD across a zone "
            "merger; a rate averages. These arms are therefore not "
            "zone-merger invariant and the specification stops being a "
            "destination-choice model in Train's strict sense. See "
            "NOTES_PERCAPITA.md section 2."),
        "interval_note": (
            "p025/p975 are PERCENTILES OVER RE-SPLITS of one fixed set of "
            "decisions. They are not standard errors and say nothing about "
            "drawing a different sample of facilities."),
    }
    dest = paths.METRICS / ARTEFACT
    dest.parent.mkdir(parents=True, exist_ok=True)
    write_json(dest, report)
    print(f"\n  -> {paths.rel(dest)}\n")
    return report


def correlations_only() -> dict:
    """The collinearity measurement alone. Seconds, not hours."""
    data, _, levels, z = build()
    corr = correlation_table(levels, SOURCES)
    print_correlations(corr)
    return {"collinearity": corr,
            "collinearity_zcta_frame": frame_correlations(z, SOURCES),
            "columns": list(data.names)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repeats", type=int, default=REPEATS)
    parser.add_argument("--no-resume", action="store_true",
                        help="discard the checkpoint and start over")
    parser.add_argument("--report-only", action="store_true",
                        help="summarise the checkpoint without fitting, so a "
                             "long run can be read while it is still going")
    parser.add_argument("--correlations-only", action="store_true",
                        help="measure the collinearity and stop")
    args = parser.parse_args(argv)
    os.nice(19)
    paths.ensure_dirs()
    configure()
    if args.correlations_only:
        correlations_only()
        return 0
    run(repeats=args.repeats, resume=not args.no_resume,
        fit=not args.report_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
