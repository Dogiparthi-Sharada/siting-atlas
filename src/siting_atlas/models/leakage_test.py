"""Does the warehousing covariate contain the outcome it predicts?

    python -m siting_atlas.models.leakage_test

THE SUSPICION, STATED PRECISELY
-------------------------------
The choice model's one working covariate is `warehousing_establishments`:
County Business Patterns' count of NAICS 493 establishments in a ZCTA. The
GBM benchmark gives that column 54.5% of its total split gain, so essentially
everything either model knows comes from it.

An Amazon delivery station IS a warehousing establishment. So if the CBP
vintage used for a decision was measured AFTER that facility opened, the
covariate counts the facility itself, and the model is being asked to predict
an event from a variable that already contains it. The prediction would look
good and mean nothing.

A lag guard exists to prevent exactly this, and `docs/data/CBP_DETAIL.md` sec.5
records that it is NOMINAL rather than real: `open_year` equals the quarter of
the earliest OSHA inspection for 104 of 104 national rows -- an UPPER bound, so
the true opening is earlier by an unknown amount -- and the guard's margin is
zero. A guard with zero margin against a date that is systematically too late
does not exclude the facility from its own covariate.

WHAT THIS MEASURES AND WHAT IT CANNOT
-------------------------------------
This is an ABLATION: refit with the covariate removed and see what is left.

  - If accuracy collapses to the no-information null, everything the model
    knows comes from a possibly-circular variable, and the headline results
    cannot be defended until the lag is fixed.
  - If accuracy holds up, the other covariates carry real signal and the
    leakage question, while still open, is not load-bearing.

An ablation cannot PROVE leakage. Contamination and genuine agglomeration
make the same prediction -- warehouses cluster where warehouses are, whether
or not this one is counted -- and no ablation separates them. The decisive
test is a CBP vintage strictly earlier than every opening, which needs real
opening dates. Those have just arrived from MWPVL (446 of them, validated at
97.2% against the OSHA bound), so the decisive test is now possible and is
named at the end of the report rather than run here.

Everything is measured over repeated splits, because a single 38-event test
set cannot separate a two-decision difference from noise.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure
from .choice import ATTRACTIONS, CBP_ATTRACTIONS, build, evaluate, fit
from .choice_runner import SEED, TEST_FRACTION, load_national

#: Enough that the standard error of the mean is well under the effect we are
#: looking for. The GBM benchmark used the same count for the same reason.
REPEATS = 50

TOP_K = 10


def _load():
    facilities = load_national()
    panel = pd.read_parquet(paths.PANEL,
                            columns=["zcta", "cbsa_code", *ATTRACTIONS])
    cbp_path = paths.INTERIM / "cbp_detail.parquet"
    if not cbp_path.exists():
        raise SystemExit(
            f"\n  {paths.rel(cbp_path)} absent, so there is no warehousing\n"
            "  covariate to ablate, and nothing to measure. Run:\n"
            "      python -m siting_atlas.ingest.cbp_detail\n")
    return facilities, panel, pd.read_parquet(cbp_path)


def _arm(facilities, panel, cbp, use_cbp: bool):
    return build(facilities, panel, cbp if use_cbp else None,
                 CBP_ATTRACTIONS if use_cbp else ())


def _one_split(data, rng) -> dict:
    order = rng.permutation(data.n_decisions)
    cut = int(round(data.n_decisions * (1 - TEST_FRACTION)))
    train = data.subset(np.sort(order[:cut]))
    test = data.subset(np.sort(order[cut:]))
    theta = np.asarray(fit(train)["theta"], float)
    out = evaluate(theta, test)
    # `evaluate` returns top-k as a RATE, not a count. Multiplying back to
    # hits keeps this comparable with choice_report.json and the GBM
    # benchmark, both of which quote "n of 38".
    out["_hits"] = out["top10"] * out["n_decisions"]
    out["_top10_uniform"] = out["top10_uniform"] * out["n_decisions"]
    return out


def main() -> int:
    # An ablation run is cheap to repeat and easy to confuse with the last
    # one. The stamp is what tells two of them apart.
    paths.ensure_dirs()
    init_run()
    configure()

    facilities, panel, cbp = _load()

    arms = {"with_warehousing": True, "without_warehousing": False}
    results: dict[str, dict] = {}
    for name, use in arms.items():
        data = _arm(facilities, panel, cbp, use)
        hits, briers, nulls = [], [], []
        for r in range(REPEATS):
            out = _one_split(data, np.random.default_rng(SEED + r))
            hits.append(out["_hits"])
            briers.append(out["brier"])
            nulls.append(out["_top10_uniform"])
        results[name] = {
            "covariates": list(data.names),
            "n_decisions": int(data.n_decisions),
            "top10_mean": float(np.mean(hits)),
            "top10_sd": float(np.std(hits, ddof=1)),
            "brier_mean": float(np.nanmean(briers)),
            "uniform_null_mean": float(np.mean(nulls)),
            "hits": [float(h) for h in hits],
        }

    a = results["with_warehousing"]
    b = results["without_warehousing"]
    paired = np.array(a["hits"]) - np.array(b["hits"])
    delta = {
        "mean_difference": float(paired.mean()),
        "sd_of_difference": float(paired.std(ddof=1)),
        "with_wins": int((paired > 0).sum()),
        "ties": int((paired == 0).sum()),
        "without_wins": int((paired < 0).sum()),
    }

    n_test = int(round(a["n_decisions"] * TEST_FRACTION))
    print("\n  === ablation: is the warehousing covariate load-bearing? ===\n")
    print(f"  {a['n_decisions']} decisions, {n_test} held out, "
          f"{REPEATS} re-splits\n")
    print(f"  {'':24} {'top-10':>10} {'sd':>8} {'Brier':>12} {'null':>10}")
    for name in ("with_warehousing", "without_warehousing"):
        r = results[name]
        label = name.replace("_", " ")
        hits = f"{r['top10_mean']:.2f}/{n_test}"
        print(f"  {label:24} {hits:>10} {r['top10_sd']:8.2f} "
              f"{r['brier_mean']:12.6f} {r['uniform_null_mean']:10.2f}")
    print(f"\n  paired difference : {delta['mean_difference']:+.2f} hits "
          f"(sd {delta['sd_of_difference']:.2f}), with-covariate wins "
          f"{delta['with_wins']}, loses {delta['without_wins']}, "
          f"ties {delta['ties']}")

    print("\n  Reading this:")
    print("    A LARGE drop when the covariate is removed means the model")
    print("    rests entirely on a variable that may contain its own outcome.")
    print("    A SMALL drop means the leakage question is not load-bearing.")
    print("    Neither outcome proves leakage -- agglomeration and")
    print("    contamination predict the same thing. The decisive test is a")
    print("    CBP vintage strictly earlier than every opening, which needs")
    print("    real opening dates; 446 arrived from MWPVL on 2026-09-14.\n")

    out = paths.METRICS / "leakage_test.json"
    write_json(out,
               {"repeats": REPEATS, "arms": results,
                "paired_difference": delta,
                "what_this_cannot_show":
                    "An ablation cannot distinguish contamination from "
                    "genuine agglomeration. Both imply the covariate "
                    "predicts. Only a CBP vintage measured before every "
                    "opening separates them."})
    print(f"  -> {paths.rel(out)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
