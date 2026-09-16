"""Do the panel's UNUSED columns beat the four the model actually reads?

    PYTHONPATH=src .venv/bin/python -m siting_atlas.models.covariate_search

The question this answers, and the one it does not
--------------------------------------------------
`NOTES_GBM_BENCHMARK.md` measured a data ceiling and said so with a
caveat in its own section 8.2: *"the data ceiling is a ceiling on FOUR
COLUMNS, not on the question."* The panel holds fifty. This module takes
the promising unused ones, adds them to the four one at a time and in
combination, and measures what each is worth on held-out decisions.

It cannot settle whether Amazon siting is predictable. It settles whether
the ceiling the GBM measured moves when the columns change.

What is being tested for, specifically
--------------------------------------
A large metro offers 300+ candidate ZIPs and most are physically
impossible — residential, no industrial land, no parcel. If the four
columns cannot tell those apart, the model spends its ranking on ZIPs
that were never in contention, and a BUILDABILITY covariate would be
worth more than another agglomeration covariate. `traffic_proximity`
(highway access), `diesel_pm` (truck corridors), `median_home_value`
(expensive implies residential implies unbuildable) and
`permit_units_total` (where construction happens) are the panel's
candidates for that role.

There is a second question attached. If `warehousing_establishments`
works as a buildability proxy rather than an agglomeration measure, a
clean land or traffic covariate might substitute for it — which would
both improve the model and retire the circularity risk
`NOTES_LEAKAGE_DECISIVE.md` priced at a ~20% haircut. The substitution
arms test exactly that.

Four measurement rules, and why each is not negotiable
------------------------------------------------------
1  EVERY ARM IS A COLUMN SUBSET OF ONE FRAME. Adding a column with gaps
   drops alternatives; an arm built on its own frame would be scored on
   easier choice sets. `covariate_frame` builds one object carrying every
   column and the arms are views of it, so the choice sets are identical
   and the paired difference is about the column alone.

2  STRATIFIED BY CHOICE-SET SIZE. Pooled lift across heterogeneous choice
   sets is a Simpson's-paradox trap that has already produced one wrong
   conclusion here (`outputs/metrics/panel_experiments.json`; the earlier
   `lift_by_market_size.json` is superseded and points at it). Small
   markets are capped near 1.5x because chance already scores ~67%.

3  SELECTION HAPPENS INSIDE THE TRAINING FOLD. See `covariate_arms`. The
   naive full-data selection is also run and is labelled optimistic,
   because the gap between the two IS the selection bias.

4  THE VINTAGE RULE APPLIES TO ANYTHING TIME-VARYING, AND ONLY TO THAT.
   `permit_units_total` and `permits_yoy_pct` move year to year, so both
   are read at the panel year strictly before the opening, and a
   decision with no earlier panel year is dropped rather than scored on
   a contemporaneous one. The other thirteen candidates take
   one value per ZCTA across all eight panel years. Time-invariance is
   not a defect for a conditional choice model — it compares
   alternatives inside one choice set at one date and never differences
   a ZCTA against its own past, so cross-sectional variation is the only
   variation it uses — and it also rules OUT the self-counting mechanism
   `NOTES_COVARIATE_LEAKAGE.md` documents, because a value that does not
   move cannot move because of the facility. What it does not rule out
   is a measurement WINDOW that post-dates the decision; see
   `covariate_frame`.

Demographic columns are held out of the headline search
-------------------------------------------------------
`low_income_pct` and `people_of_colour_pct` are in the panel and are
tested, in an arm of their own. They are not offered to the search that
produces the headline specification. A model that predicts where a
warehouse goes from who lives there is a different object from one that
predicts it from land and industry; this project exists to help
communities evaluate siting decisions, and that makes the inclusion a
choice to argue in the open rather than one for a greedy search to make
by itself. Both are reported either way, so nothing is hidden by the
separation.

The specification limit this search runs into
---------------------------------------------
`choice.py` enforces ``beta_k = exp(theta_k) > 0``. A column that REPELS
cannot be expressed: the optimiser walks it to the boundary and it reads
as worthless when it may be strongly informative with the other sign.
`median_home_value` and `diesel_pm` are both plausibly repellent, so each
is entered twice — as the level and as ``1/x``. That is a workaround and
is reported as one; ``1/x`` is a different functional form, not a sign
flip, and it is intensive, which breaks the aggregation invariance
`MODEL_SPEC.md` section 1 says the ``ln(beta'a)`` form exists to keep.
"""

from __future__ import annotations

import argparse

import pandas as pd

from ..common import paths
from ..common.logging_setup import configure
from ..warehouse.national import load_national
from .choice import ATTRACTIONS, CBP_ATTRACTIONS
from .choice_runner import SEED, TEST_FRACTION
from .covariate_arms import forward_select
from .covariate_audit import audit, print_audit
from .covariate_frame import (
    DEMOGRAPHIC,
    INV,
    RECIPROCALS,
    STATIC_CANDIDATES,
    VARYING_CANDIDATES,
    VARYING_SOURCE,
    build_frame,
    load_panel,
    static_frame,
)
from .covariate_harness import (
    LEDGER_NOTE,
    REPEATS,
    STAGES,
    ledger,
    load,
    run_experiment,
    save,
)
from .covariate_permits import attrition, permit_spec, print_attrition

EXPANDED = (paths.ROOT / "data" / "external" / "facility_panel"
            / "national_facilities_expanded.csv")

BASE = (*ATTRACTIONS, *CBP_ATTRACTIONS)
NO_WAREHOUSING = ATTRACTIONS

#: Everything offered, including the two reciprocals.
CANDIDATES = (*STATIC_CANDIDATES, *(INV + c for c in RECIPROCALS))

#: What the HEADLINE search is allowed to pick from. The demographic
#: columns are held out of it deliberately — see `covariate_frame`.
NEUTRAL = tuple(c for c in CANDIDATES if c not in DEMOGRAPHIC)


def _load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not EXPANDED.exists():
        raise SystemExit(f"\n  {paths.rel(EXPANDED)} not found\n  run: "
                         "python -m siting_atlas.warehouse.mwpvl_merge\n")
    cbp_path = paths.INTERIM / "cbp_detail.parquet"
    if not cbp_path.exists():
        raise FileNotFoundError(
            f"{paths.rel(cbp_path)} is missing; without it the baseline is "
            "three covariates and nothing here is comparable to the "
            "published number. Run python -m siting_atlas.ingest.cbp_detail")
    panel = load_panel(paths.PANEL, STATIC_CANDIDATES, VARYING_CANDIDATES)
    return load_national(EXPANDED), panel, pd.read_parquet(cbp_path)


def _core_spec() -> dict:
    fixed = {"baseline": list(BASE), "no_warehousing": list(NO_WAREHOUSING)}
    for col in CANDIDATES:
        fixed[f"+ {col}"] = [*BASE, col]
    return {"fixed": fixed, "search": {
        "forward (nested, honest)": {"base": list(BASE),
                                     "candidates": list(NEUTRAL)},
        "forward, no warehousing": {"base": list(NO_WAREHOUSING),
                                    "candidates": list(NEUTRAL)},
        "forward + demographics": {"base": list(BASE),
                                   "candidates": list(CANDIDATES)}}}


def run(workers: int = 5, stages: tuple[str, ...] = STAGES,
        resume: bool = True) -> dict:
    """Run the requested stages, reusing any already in the artefact."""
    report: dict = load() if resume else {}
    facilities, panel, cbp = _load()
    report |= {"seed": SEED, "repeats": REPEATS,
               "test_fraction": TEST_FRACTION,
               "facilities": int(len(facilities)),
               "stage_ledger": ledger(report, tuple(stages)),
               "stage_ledger_note": LEDGER_NOTE}
    report.pop("stages_present", None)

    if "audit" in stages:
        report["column_audit"] = audit(
            panel, (*ATTRACTIONS, *STATIC_CANDIDATES,
                    *dict.fromkeys(VARYING_SOURCE[c]
                                   for c in VARYING_CANDIDATES)))
        print_audit(report["column_audit"])
        save(report)

    if "anchor" in stages:
        anchor, cov = build_frame(facilities, panel, cbp, CBP_ATTRACTIONS)
        report["anchor"] = run_experiment(
            "ANCHOR: the published four columns, full frame", anchor, cov,
            {"fixed": {"baseline": list(BASE)}}, "baseline", workers)
        save(report)

    if not ({"core", "naive", "permits"} & set(stages)):
        # The metadata block and the stage ledger are refreshed on every
        # invocation, including one that runs no stage at all, so an
        # artefact assembled across several invocations still says so.
        save(report)
        return report
    core, cov = build_frame(facilities, panel, cbp, CBP_ATTRACTIONS,
                            static=STATIC_CANDIDATES,
                            reciprocals=RECIPROCALS)
    if "core" in stages:
        report["core"] = run_experiment(
            "CORE: thirteen unused time-constant columns, one frame",
            core, cov, _core_spec(), "baseline", workers)
        save(report)

    if "naive" in stages:
        naive, trace = forward_select(core, BASE, NEUTRAL, SEED)
        report["naive_selection"] = {
            "columns": list(naive), "trace": trace,
            "warning": "selected on the WHOLE frame, so its held-out gain "
                       "is optimistic by an unmeasured amount. Reported "
                       "only as the contrast to the nested search."}
        save(report)

    if "permits" in stages:
        naive = tuple(report["naive_selection"]["columns"])
        permit, cov = build_frame(facilities, panel, cbp, CBP_ATTRACTIONS,
                                  static=STATIC_CANDIDATES,
                                  varying=VARYING_CANDIDATES,
                                  reciprocals=RECIPROCALS)
        kept = set(static_frame(panel, STATIC_CANDIDATES,
                                RECIPROCALS)["zcta"])
        report["permit_attrition"] = attrition(core, permit, panel, kept)
        print_attrition(report["permit_attrition"])
        report["permits"] = run_experiment(
            "PERMITS: time-varying, read at the pre-opening vintage",
            permit, cov, permit_spec(BASE, naive), "baseline", workers)
        save(report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--stages", nargs="*", choices=STAGES,
                        default=list(STAGES),
                        help="stages to run; the rest are read from the "
                             "existing artefact")
    parser.add_argument("--workers", type=int, default=5)
    args = parser.parse_args(argv)
    paths.ensure_dirs()
    configure()
    run(workers=args.workers, stages=tuple(args.stages))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
