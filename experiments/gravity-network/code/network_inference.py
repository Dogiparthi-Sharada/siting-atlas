"""Proper inference on the arm that produced the project's one exclusion.

    python -m siting_atlas.models.network_inference

What is at stake
----------------
`NOTES_PANEL_EXPERIMENTS.md` §3.1 reports `combined_plus_network`'s
`warehousing_establishments` at **1.401 [1.037, 1.868]** and calls it the
first interval in this project's history that does not contain the
numeraire. That bracket is the 2.5th and 97.5th PERCENTILE OVER 50
RE-SPLITS of the same 485 decisions. It is not a standard error, the
notes say so twice (§3.1 reading 2, §9 item 1), and §9 item 1 names the
test that had not been run: `choice_inference`'s metro-clustered
bootstrap. This module runs it.

Three reasons the re-split spread and a bootstrap interval are not the
same quantity, all of which push the same way:

1. A re-split spread measures how much the estimate moves with WHICH 60%
   of the decisions are in the training half. A bootstrap measures how
   much it moves when the decisions themselves are redrawn. The first is
   a subsample of a fixed sample; only the second is aiming at sampling
   variability.
2. The 50 re-splits are not independent. They resample the same 485
   decisions, so the spread is shrunk by the overlap.
3. Decisions cluster in metros -- 485 of them sit in 194 -- and
   `choice_runner` prints a warning about exactly this. Neither the
   re-split spread nor the per-decision bootstrap accounts for it.

And one that pushes the other way, so the comparison is not stacked: the
re-split fits use 291 training decisions each and the bootstrap uses all
485, which should make the bootstrap TIGHTER. If it is wider anyway, the
finding is not an artefact of the comparison.

The second arm
--------------
§7 of the same notes names `combined_plus_network` on the `mwpvl_clean`
filter as the obvious next arm and records that it was never run. It is
run here, on the same three measures, stratified by choice-set size with
distinct-decision n, and with the same clustered bootstrap.

The theoretical cost
--------------------
Measured, not asserted, in `network_merge.py`, and reported in §2 of the
console output and the `merger_invariance` block of the artefact.
"""

from __future__ import annotations

import numpy as np

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer
from .choice import CBP_ATTRACTIONS, fit
from .choice_bootstrap import ALPHA, endpoint_errors, metro_clusters
from .choice_inference import TRAIN_PRECONDITION, _interval
from .choice_runner import SEED
from .choice_sandwich import BOUNDARY_TOL, sandwich
from .network_bootstrap import R_CAP, agreement_check, parallel_bootstrap
from .network_data import NETWORK_ARMS, build_network_arms
from .network_merge import MERGE_DRAWS, additivity_error, merge_drift
from .network_print import report_text
from .network_resplit import (
    SPREAD_IS_NOT_A_STANDARD_ERROR,
    paired_against,
    panel_blob,
    published_spread,
    strata,
)
from .network_sandwich import clustered_sandwich
from .network_sensitivity import (
    SENSITIVITY_DRAWS,
    drop_two_sensitivity,
)
from .panel_harness import REPEATS, measure

_log = get_logger("models.network_inference")

WAREHOUSING = CBP_ATTRACTIONS[0]

OUT_PATH = paths.METRICS / "network_inference.json"

NO_DECISION_BOOTSTRAP = (
    "Not run, and the omission is declared rather than hidden. The "
    "question this module exists to answer is what happens when the "
    "metro clustering `choice_runner` warns about is respected, and the "
    "metro-clustered bootstrap answers it. The per-decision bootstrap is "
    "the comparison, and the SAME comparison is available analytically "
    "and for free from the two sandwiches, which differ only in whether "
    "the meat is summed over decisions or over metros -- see "
    "`sandwich_over_decisions` against `sandwich_over_metros` and the "
    "`se_ratio_vs_independent_decisions` field. It costs about 8 "
    "wall-seconds a replicate against the clustered bootstrap's 4.5, one "
    "attempt had a pool worker killed by the host part way through, and "
    "it would not change any verdict in this artefact. Pass "
    "with_decision_bootstraps=True to run it.")


def _fit_block(d, seed: int, cap: int) -> tuple:
    """Everything that costs seconds: the fit and both sandwiches.

    Split from the bootstrap on purpose. The bootstrap costs hours, so
    the artefact is written once this part exists and again after every
    stage that follows; a run stopped early then leaves a file that says
    what it managed rather than nothing at all.
    """
    fitted = fit(d)
    theta = np.asarray(fitted["theta"], float)
    clusters = metro_clusters(d)
    names = tuple(n for n in d.names if n != fitted["numeraire"])
    return {
        "n_decisions": int(d.n_decisions),
        "n_alternatives": int(len(d.a)),
        "n_metros": int(len(np.unique(clusters))),
        "seed": seed, "alpha": ALPHA, "replicate_cap": int(cap),
        "fit": {k: fitted[k] for k in
                ("beta", "theta", "log_likelihood", "log_likelihood_uniform",
                 "mcfadden_rho_squared", "converged", "n_decisions")},
        "replicates": {}, "parameters": {},
        "sandwich_over_decisions": sandwich(theta, d, names, ALPHA),
        "sandwich_over_metros": clustered_sandwich(theta, d, names,
                                                   clusters, ALPHA),
        "train_precondition": TRAIN_PRECONDITION,
    }, theta, clusters


def _add_bootstrap(block: dict, d, theta: np.ndarray, clusters, kind: str,
                   seed: int, cap: int) -> None:
    """One bootstrap, folded into an existing arm block.

    ``kind`` is "metros" or "decisions". The metro one is run first
    everywhere because it is the one `NOTES_PANEL_EXPERIMENTS.md` §9 item
    1 asked for; the per-decision one is the comparison.
    """
    metros = kind == "metros"
    boot = parallel_bootstrap(d, theta, seed + (101 if metros else 0),
                              cluster=clusters if metros else None, cap=cap)
    block["replicates"][kind] = {
        k: boot[k] for k in ("replicates", "settled", "capped", "n_units",
                             "seconds")}
    beta = np.exp(theta)
    at_boundary = beta <= BOUNDARY_TOL
    for k, name in enumerate(d.names[1:]):
        draws = boot["beta"][:, k]
        p = block["parameters"].setdefault(
            name, {"beta_point": float(beta[k]),
                   "at_boundary": bool(at_boundary[k])})
        p[f"bootstrap_over_{kind}"] = _interval(
            draws, beta[k], at_boundary[k], seed)
        if metros:
            p["metro_endpoint_mcse"] = endpoint_errors(draws, seed + 7)
            p["share_of_metro_replicates_at_boundary"] = float(
                (draws < BOUNDARY_TOL).mean())


def _dump(report: dict, stage: str) -> None:
    """Write the artefact as it stands. Called after every stage."""
    report["stages_completed"] = [*report.get("stages_completed", []), stage]
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(OUT_PATH, report)
    _log.info("stage %s written to %s", stage, paths.rel(OUT_PATH))


def _second_arm(report: dict, state: tuple, panel: dict, mix,
                repeats: int) -> None:
    """The three measures on `mwpvl_clean_plus_network`."""
    arm = "mwpvl_clean_plus_network"
    d1, _, _, entry1 = state
    measured = measure(d1, repeats)
    reference = mix or measured["size_mix"]
    block = report["arms"][arm]
    block["three_measures"] = strata(d1, measured, reference)
    block["three_measures"]["reference_mix"] = reference
    block["resplit_spread"] = {
        "beta_mean": measured["beta_mean"],
        "beta_p025": measured["beta_p025"],
        "beta_p975": measured["beta_p975"],
        "warning": SPREAD_IS_NOT_A_STANDARD_ERROR}
    base_arm = panel.get("arms", {}).get(entry1["baseline_arm"])
    block["baseline_resplit_spread"] = published_spread(
        entry1["baseline_arm"], panel)
    block["paired_against_baseline"] = (
        paired_against(measured, base_arm) if base_arm
        and entry1["checks"]["decision_sets_identical"]
        else {"comparable": False})


def run(cap: int = R_CAP, repeats: int = REPEATS,
        merge_draws: int = MERGE_DRAWS,
        sensitivity_draws: int = SENSITIVITY_DRAWS,
        with_decision_bootstraps: bool = False) -> dict:
    """Stages, in the order a run that has to be stopped early should go.

    The metro-clustered bootstrap on `combined_plus_network` is the
    question; it goes first. The per-decision bootstraps are the
    comparison and go last, because the same comparison is available
    analytically from the two sandwiches at no cost.
    """
    with traced_layer("L5", "network-arm inference"):
        with step("network_inf:build"):
            built = build_network_arms()
        panel = panel_blob()
        mix = panel.get("reference_mix")

        report: dict = {
            "seed": SEED, "replicate_cap": cap, "repeats": repeats,
            "network_facilities": built["network_facilities"],
            "spread_is_not_a_standard_error": SPREAD_IS_NOT_A_STANDARD_ERROR,
            "per_decision_bootstrap": (
                {"run": True} if with_decision_bootstraps
                else {"run": False, "reason": NO_DECISION_BOOTSTRAP}),
            "arms": {},
        }
        state = {}
        for arm in NETWORK_ARMS:
            entry = built["arms"][arm]
            block, theta, clusters = _fit_block(entry["data"], SEED, cap)
            state[arm] = (entry["data"], theta, clusters, entry)
            block["checks"] = entry["checks"]
            block["provenance"] = entry["provenance"]
            block["published_resplit_spread"] = published_spread(
                arm, panel)
            report["arms"][arm] = block
        _dump(report, "fits_and_sandwiches")

        d0, theta0, clusters0, entry0 = state["combined_plus_network"]
        with step("network_inf:agreement"):
            report["parallel_matches_sequential"] = agreement_check(
                d0, theta0, SEED)
        _dump(report, "parallel_agreement")

        with step("network_inf:facility_set_sensitivity"):
            report["facility_set_sensitivity"] = drop_two_sensitivity(
                built["frames"]["combined_plus_network"], built["panel"],
                built["cbp"], SEED, sensitivity_draws)
        _dump(report, "facility_set_sensitivity")

        with step("network_inf:headline_metro_bootstrap"):
            _add_bootstrap(report["arms"]["combined_plus_network"], d0,
                           theta0, clusters0, "metros", SEED, cap)
        _dump(report, "combined_plus_network_metros")

        with step("network_inf:merger"):
            base0 = entry0["baseline"]
            base_theta = np.asarray(fit(base0)["theta"], float)
            report["merger_invariance"] = {
                "network": additivity_error(d0, theta0, clusters0, SEED),
                "extensive_only_control": additivity_error(
                    base0, base_theta, clusters0, SEED),
                "drift_under_a_redrawn_map": merge_drift(
                    {"combined_plus_network": (d0, theta0),
                     "combined_extensive_only": (base0, base_theta)},
                    clusters0, WAREHOUSING, SEED, merge_draws),
            }
        _dump(report, "merger_invariance")

        arm2 = "mwpvl_clean_plus_network"
        with step(f"network_inf:{arm2}:metros"):
            d1, theta1, clusters1, _ = state[arm2]
            _add_bootstrap(report["arms"][arm2], d1, theta1, clusters1,
                           "metros", SEED, cap)
        _dump(report, f"{arm2}_metros")

        with step(f"network_inf:{arm2}:three_measures"):
            _second_arm(report, state[arm2], panel, mix, repeats)
        _dump(report, f"{arm2}_three_measures")

        if with_decision_bootstraps:
            with step("network_inf:decision_bootstraps"):
                _add_bootstrap(report["arms"]["combined_plus_network"], d0,
                               theta0, clusters0, "decisions", SEED, cap)
                _dump(report, "combined_plus_network_decisions")
                _add_bootstrap(report["arms"][arm2], d1, theta1, clusters1,
                               "decisions", SEED, cap)
            _dump(report, f"{arm2}_decisions")

    w = report["arms"]["combined_plus_network"]["parameters"][WAREHOUSING]
    metric("network_warehousing_metro_excludes_one",
           float(w["bootstrap_over_metros"].get("excludes_ratio_one", False)))
    artefact(OUT_PATH, arms=len(report["arms"]))
    return report


def main() -> int:
    paths.ensure_dirs()
    init_run()
    configure()
    print(report_text(run()))
    print(f"  -> {paths.rel(OUT_PATH)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
