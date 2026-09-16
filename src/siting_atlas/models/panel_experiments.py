"""Which composition of the facility panel gives the best model?

    python -m siting_atlas.models.panel_experiments

The question
------------
`NOTES_EXPANDED_REFIT.md` refitted the choice model on a panel grown from
104 to 700 facilities and found the headline coefficient got LESS
impressive: `warehousing_establishments` 1.528 [0.985, 2.550] ->
1.170 [0.895, 1.455], an interval 64% narrower that still spans the
numeraire. That run compared two frames. This one compares five, so the
effect of SOURCE, of OCR error, of date provenance and of market mix can
be told apart, and adds a covariate the model has never had. The five
arms and how each is filtered are declared in `panel_arms.py`.

What is read, and in what order
-------------------------------
Three measures of "a better model", ranked the way the brief ranks them,
and they are allowed to disagree:

    1  coefficient precision -- interval width, and whether it excludes
       1.0, the numeraire
    2  predictive lift over the arm's OWN chance rate, STRATIFIED by
       choice-set size and standardised to a common mix (`panel_strata`
       explains why a pooled lift would rank the arms on composition)
    3  Brier

Raw top-k is NOT comparable across arms: the arms hold different choice
sets, and a top-10 count is a property of the choice set before it is a
property of the model. The raw numbers are in the artefact because they
are the inputs to everything else; they are not a ranking.

Two algorithms, because a difference between arms could be either
------------------------------------------------------------------
The conditional logit is the structural model: interpretable, scale
invariant, and the only one that produces a coefficient interval, which
is measure 1 above. LightGBM's `lambdarank` is the flexible
benchmark `MODEL_SPEC.md` §9.4 commissioned. Running both on every arm
separates "this arm has better data" from "this arm suits this
functional form". `NOTES_GBM_BENCHMARK.md` found a data ceiling with a
~1-decision model term at 56 training decisions; whether that survives
at 291 is a question only the bigger arms can answer. `panel_harness`
holds the split protocol and says which two of that benchmark's six
configurations are run, and why.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, step, traced_layer
from .choice import ATTRACTIONS, CBP_ATTRACTIONS, build
from .choice_runner import SEED
from .panel_arms import ARM_NAMES, arm_frames, drop_profile
from .panel_harness import LOGIT, REPEATS, measure
from .panel_network import (
    NETWORK_COLUMNS,
    augment_cbp,
    load_network_facilities,
    vintage_table,
)
from .panel_print import report_text
from .panel_strata import standardise

_log = get_logger("models.panel_experiments")

#: The arm whose choice-set-size mix every arm is standardised to.
REFERENCE_ARM = "combined"

#: `panel_network.COUNT_RADIUS_MILES` is a choice. These are the two it
#: is varied against: the cost model's last-mile `default_linehaul_miles`
#: below it, and twice the primary above it.
RADIUS_SENSITIVITY = (25.0, 50.0, 100.0)

WAREHOUSING = CBP_ATTRACTIONS[0]

MWPVL_INTERIM = paths.INTERIM / "mwpvl_facilities.csv"


def _panel_and_cbp():
    panel = pd.read_parquet(paths.PANEL,
                            columns=["zcta", "cbsa_code", *ATTRACTIONS])
    cbp_path = paths.INTERIM / "cbp_detail.parquet"
    if not cbp_path.exists():
        raise SystemExit(
            f"\n  {paths.rel(cbp_path)} not found\n  run: python -m "
            "siting_atlas.ingest.cbp_detail\n")
    return panel, pd.read_parquet(cbp_path)


def _geography() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """ZCTA centroids, the candidates, and the placeable non-DS network."""
    centroids = (pd.read_parquet(
        paths.PANEL, columns=["zcta", "cbsa_code", "latitude", "longitude"])
        .drop_duplicates("zcta"))
    candidates = centroids.dropna(
        subset=["cbsa_code", "latitude", "longitude"])
    facilities, diagnostics = load_network_facilities(
        MWPVL_INTERIM, centroids.set_index("zcta")[["latitude", "longitude"]])
    return candidates, facilities, diagnostics


def _network_cbp(cbp: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """CBP vintages extended and joined to the prior-network covariates."""
    candidates, facilities, diagnostics = _geography()
    table = vintage_table(candidates, facilities)
    diagnostics["candidate_zctas"] = int(len(candidates))
    diagnostics["vintages"] = int(table["cbp_year"].nunique())
    return augment_cbp(cbp, table, CBP_ATTRACTIONS), diagnostics


def _candidate_zctas(panel: pd.DataFrame) -> set:
    """The ZCTAs `choice.build` will admit as alternatives.

    Reproduced rather than imported because `build` computes it inline.
    A ZCTA that fails this filter is not merely missing a covariate: it
    cannot appear in any choice set, so a facility sited in it has no
    usable choice set at all.
    """
    zctas = panel.drop_duplicates("zcta").dropna(subset=["cbsa_code"])
    for col in ATTRACTIONS:
        zctas = zctas[zctas[col].notna() & (zctas[col] > 0)]
    return set(zctas["zcta"].astype(str))


def _drop_ledger(facilities: pd.DataFrame, home: set,
                 vintages: list[int]) -> dict:
    """Where an arm's facilities go between the file and the fit.

    `NOTES_EXPANDED_REFIT.md` §8 item 3 records that this ledger was
    measured by hand and never emitted. It is emitted here.
    """
    zcta = facilities["zcta"].astype(str).str.strip()
    year = pd.to_numeric(facilities.get("open_year"), errors="coerce")
    in_panel = zcta.isin(home)
    dated = in_panel & year.notna()
    usable = dated & (year > min(vintages))
    return {
        "facilities_loaded": int(len(facilities)),
        "dropped_no_panel_zcta": int((~in_panel).sum()),
        "dropped_no_numeric_open_year": int((in_panel & ~year.notna()).sum()),
        "dropped_no_earlier_cbp_vintage": int((dated & ~usable).sum()),
        "reaching_the_fit": int(usable.sum()),
    }


def _radius_sensitivity(frame: pd.DataFrame, panel: pd.DataFrame,
                        cbp: pd.DataFrame, mix: dict,
                        repeats: int) -> dict:
    """Is the network result an artefact of the 50-mile count radius?

    The radius is a choice, not a sourced constant (`panel_network`
    says so), so the honest thing is to vary it and print all three.
    The logit only: the question is about the covariate, and a second
    algorithm would not make the radius less arbitrary.
    """
    candidates, facilities, _ = _geography()
    out = {}
    for radius in RADIUS_SENSITIVITY:
        table = vintage_table(candidates, facilities, radius)
        data = build(frame, panel, augment_cbp(cbp, table, CBP_ATTRACTIONS),
                     CBP_ATTRACTIONS + NETWORK_COLUMNS)
        arm = measure(data, repeats, with_gbm=False)
        block = arm["methods"][LOGIT]
        out[f"radius_{int(radius)}mi"] = {
            "standardised_top10": standardise(block["strata"], mix)["top10"],
            "raw_pooled": block["raw_pooled"],
            "beta_mean": arm["beta_mean"],
            "beta_p025": arm["beta_p025"],
            "beta_p975": arm["beta_p975"],
        }
    return out


def _network_gain(arms: dict, comparable: bool) -> dict:
    """What the network covariates bought, as a PAIRED difference.

    This is the one comparison in the file that is genuinely paired:
    `combined` and `combined_plus_network` hold the identical decisions
    and take the identical splits from the identical seeds, so the
    market-mix problem that makes every other cross-arm comparison
    invalid does not arise here. A repeat that drew easy decisions
    inflates both rows and the difference removes it.

    The win-loss record is NOT a sign test. The 50 re-splits resample
    the same decisions and are not independent -- the same caveat
    `NOTES_GBM_BENCHMARK.md` §8 item 4 attaches to its own W-L records.
    """
    if not comparable:
        return {"comparable": False,
                "reason": "the two arms do not hold the same decisions, so "
                          "a paired difference would not be paired"}
    base = arms["combined"]["methods"]
    plus = arms["combined_plus_network"]["methods"]
    out: dict = {"comparable": True, "methods": {}}
    for method, block in base.items():
        rows = {}
        for key in block["per_repeat"]:
            diff = (np.asarray(plus[method]["per_repeat"][key])
                    - np.asarray(block["per_repeat"][key]))
            better = diff < 0 if key == "brier" else diff > 0
            rows[key] = {
                "higher_is_better": key != "brier",
                "paired_mean_difference": float(diff.mean()),
                "paired_sd": float(diff.std(ddof=1)),
                "repeats_improved": int(better.sum()),
                "repeats_worsened": int((diff != 0).sum() - better.sum()),
            }
        rows["standardised_top10_lift"] = {
            "combined": block["standardised"]["top10"]["lift"],
            "combined_plus_network": (
                plus[method]["standardised"]["top10"]["lift"]),
        }
        out["methods"][method] = rows
    return out


def run(repeats: int = REPEATS) -> dict:
    with traced_layer("L5", "panel composition experiments"):
        with step("panel_exp:load"):
            panel, cbp = _panel_and_cbp()
            frames, provenance = arm_frames()
            net_cbp, net_diag = _network_cbp(cbp)
            vintages = sorted(cbp["cbp_year"].unique().tolist())
            home = _candidate_zctas(panel)

        arms, ids, columns = {}, {}, {}
        for name in ARM_NAMES:
            with step(f"panel_exp:{name}"):
                network = name == "combined_plus_network"
                extra = (CBP_ATTRACTIONS + NETWORK_COLUMNS if network
                         else CBP_ATTRACTIONS)
                data = build(frames[name], panel,
                             net_cbp if network else cbp, extra)
                ids[name] = list(data.ids)
                columns[name] = data.a[:, data.names.index(WAREHOUSING)].copy()
                arms[name] = measure(data, repeats)
                arms[name].update(provenance[name])
                arms[name]["ledger"] = _drop_ledger(
                    frames[name], home, vintages)

        reference_mix = arms[REFERENCE_ARM]["size_mix"]
        with step("panel_exp:radius"):
            radius = _radius_sensitivity(frames["combined"], panel, cbp,
                                         reference_mix, repeats)

    for arm in arms.values():
        for block in arm["methods"].values():
            block["standardised"] = standardise(block["strata"],
                                                reference_mix)
    same_ids = ids["combined"] == ids["combined_plus_network"]
    report = {
        "repeats": repeats, "seed": SEED,
        "reference_mix_arm": REFERENCE_ARM, "reference_mix": reference_mix,
        "network_covariates": {
            "columns": list(NETWORK_COLUMNS), **net_diag},
        "arms": arms,
        "network_gain": _network_gain(arms, bool(same_ids)),
        "radius_sensitivity": radius,
        # The network arm extends the CBP vintages to 2030 by carrying the
        # 2022 slab forward. If that changed the warehousing covariate or
        # the decision set, arm 5 would not be arm 4 plus a covariate and
        # the difference between them would not be attributable.
        "decision_sets_identical_combined_vs_network": bool(same_ids),
        "warehousing_identical_combined_vs_network": bool(
            same_ids and np.allclose(columns["combined"],
                                     columns["combined_plus_network"])),
        "mwpvl_clean_subset_of_mwpvl_only": (
            set(ids["mwpvl_clean"]) <= set(ids["mwpvl_only"])),
        "drop_profile": drop_profile(),
        "reporting_rule": (
            "Raw Brier PAIR and top-k against a uniform-within-choice-set "
            "null, never a skill score: Gneiting & Raftery (2007) Sec. 2.3 "
            "p.362. Raw top-k is NOT comparable across arms -- the arms "
            "hold different choice sets. Compare on the standardised lift, "
            "the stratum lifts with their n, and the coefficient intervals."),
    }
    out = paths.METRICS / "panel_experiments.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, report)
    artefact(out, arms=len(arms))
    return report


def main() -> int:
    paths.ensure_dirs()
    init_run()
    configure()
    print(report_text(run()))
    print(f"  -> {paths.rel(paths.METRICS / 'panel_experiments.json')}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
