"""Refit the choice model on the MWPVL-expanded panel, and compare.

    python -m siting_atlas.models.refit_expanded

WHAT THIS IS FOR
----------------
The conditional choice model's binding constraint has always been sample size,
not specification. 104 national facilities give 94 usable decisions, 38 of them
held out, against 5 parameters -- 7.6 events per parameter, under the
conventional floor of 10. That is why `choice_sandwich` cannot distinguish the
fitted covariate from its own numeraire (interval 0.73 to 2.83 against a null
of 1, p = 0.287) and why a single 38-event test set cannot separate a
two-decision difference from noise.

`warehouse/mwpvl_merge` raises the panel by several hundred rows. Whether
that removes the constraint or merely moves it is the question here, and it
is worth asking carefully rather than assuming the bigger number is better.

The size is deliberately NOT quoted in this docstring. It was, once — "658
rows, 503 of them dated and placed in a CBSA" — and both figures went stale
inside a week as the OCR pipeline went from two parsed tables to thirteen.
The live counts are `arms.*.rows_in_file` and `arms.*.facilities` in the
artefact this module writes, and `panel_rows_after` in
`outputs/metrics/mwpvl_merge.json`. Cite those.

WHY THE COMPARISON IS RUN BOTH WAYS
-----------------------------------
Both panels are fitted here, with the same code, the same seed and the same
evaluation, so the difference between them is the panel and nothing else.
Quoting a new headline without the old one beside it would make an
incomparable number look like an improvement.

THE THREE REASONS THE NEW NUMBER COULD BE WORSE, AND SHOULD BE
--------------------------------------------------------------
Stated in advance so they are not rediscovered as excuses afterwards.

1. The added rows are OCR'd. `mwpvl_merge` reports rows that entered
   unscreened because the OCR lost their street name, duplicates its screen
   could not resolve, and a ~3% row-merge defect. The counts move every time
   the OCR is re-run, so read them from
   `outputs/metrics/mwpvl_merge.json` -- `screenability`,
   `internal_duplicates_dropped`, `held_for_clerical_review` -- rather than
   from here.
2. A large minority of rows carry no numeric opening year, which is why the
   expanded file does not pass `ingest/facility_check` (that artefact's
   `facility_check.errors` carries the current count). They contribute a
   location and no date.
3. A bigger, noisier sample can lower accuracy while IMPROVING inference. Top-k
   on a harder, wider set of decisions is not comparable to top-k on a curated
   one, and the honest reading of a drop is "the old sample was easier", not
   "the new data is bad".

So the thing to read is not which top-10 is higher. It is whether the
coefficient intervals finally exclude the numeraire -- that is what the extra
sample was for.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure
from ..warehouse.national import NATIONAL_PATH, load_national
from .choice import ATTRACTIONS, CBP_ATTRACTIONS, build, evaluate, fit
from .choice_runner import SEED, TEST_FRACTION

EXPANDED = (paths.ROOT / "data" / "external" / "facility_panel"
            / "national_facilities_expanded.csv")

#: A single split at n=38 cannot separate two decisions from noise; the GBM
#: benchmark and the leakage ablation both use 50 for the same reason.
REPEATS = 50


def _panel_and_cbp():
    panel = pd.read_parquet(paths.PANEL,
                            columns=["zcta", "cbsa_code", *ATTRACTIONS])
    cbp_path = paths.INTERIM / "cbp_detail.parquet"
    cbp = pd.read_parquet(cbp_path) if cbp_path.exists() else None
    return panel, cbp


def _measure(data, repeats: int = REPEATS) -> dict:
    """Top-10 hits and Brier over repeated splits, refitting each time."""
    hits, nulls, briers, thetas = [], [], [], []
    for r in range(repeats):
        rng = np.random.default_rng(SEED + r)
        order = rng.permutation(data.n_decisions)
        cut = int(round(data.n_decisions * (1 - TEST_FRACTION)))
        train = data.subset(np.sort(order[:cut]))
        test = data.subset(np.sort(order[cut:]))
        fitted = fit(train)
        theta = np.asarray(fitted["theta"], float)
        out = evaluate(theta, test)
        hits.append(out["top10"])
        nulls.append(out["top10_uniform"])
        briers.append(out["brier"])
        thetas.append(theta)
    n_test = int(round(data.n_decisions * TEST_FRACTION))
    theta_arr = np.vstack(thetas)
    return {
        "n_decisions": int(data.n_decisions),
        "n_test": n_test,
        "covariates": list(data.names),
        # Rates, so the two panels are comparable despite different test sizes.
        "top10_rate": float(np.mean(hits)),
        "top10_rate_sd": float(np.std(hits, ddof=1)),
        "top10_uniform_rate": float(np.mean(nulls)),
        "brier": float(np.mean(briers)),
        "beta_mean": {name: float(np.exp(theta_arr[:, i]).mean())
                      for i, name in enumerate(data.names[1:])},
        "beta_p025": {name: float(np.percentile(np.exp(theta_arr[:, i]), 2.5))
                      for i, name in enumerate(data.names[1:])},
        "beta_p975": {name: float(np.percentile(np.exp(theta_arr[:, i]), 97.5))
                      for i, name in enumerate(data.names[1:])},
    }


def main() -> int:
    # Two refits of two panels produce two artefacts that differ only in the
    # numbers. Stamping says which run each one came from.
    paths.ensure_dirs()
    init_run()
    configure()

    if not EXPANDED.exists():
        raise SystemExit(
            f"\n  {paths.rel(EXPANDED)} not found\n  run: python -m "
            "siting_atlas.warehouse.mwpvl_merge\n")

    panel, cbp = _panel_and_cbp()
    cbp_names = CBP_ATTRACTIONS if cbp is not None else ()

    out = {}
    for label, path in (("original", NATIONAL_PATH), ("expanded", EXPANDED)):
        facilities = load_national(path)
        data = build(facilities, panel, cbp, cbp_names)
        out[label] = _measure(data)
        # Provenance as FIELDS, not baked into the key. The arms used to be
        # called "original_104" and "expanded_658"; by 2026-09-15 the second
        # file held 693 rows and the key still said 658, because a re-run
        # refreshes a value and can never refresh a key. Both counts now sit
        # where the next run will correct them, and `facilities` is smaller
        # than `rows_in_file` by the E_operating_by exclusions.
        out[label]["source_file"] = paths.rel(path)
        out[label]["rows_in_file"] = int(len(pd.read_csv(path, dtype=str)))
        out[label]["facilities"] = int(len(facilities))

    a, b = out["original"], out["expanded"]
    print("\n  === choice model: original panel vs MWPVL-expanded ===\n")
    print(f"  {'':22} {'original':>10} {'expanded':>10}")
    for row, key in (("rows in file", "rows_in_file"),
                     ("facilities", "facilities"),
                     ("decisions", "n_decisions"),
                     ("held out", "n_test")):
        print(f"  {row:22} {a[key]:>10d} {b[key]:>10d}")
    for row, key in (("top-10 rate", "top10_rate"),
                     ("  uniform null", "top10_uniform_rate")):
        print(f"  {row:22} {100 * a[key]:9.1f}% {100 * b[key]:9.1f}%")
    print(f"  {'Brier':22} {a['brier']:10.6f} {b['brier']:10.6f}")

    print("\n  coefficients (ratio to households, the numeraire):")
    print("  a value whose interval EXCLUDES 1.0 is distinguishable from")
    print("  the numeraire -- which nothing in the original panel achieved.\n")
    for label in ("original", "expanded"):
        print(f"    {label}")
        r = out[label]
        for name in r["beta_mean"]:
            lo, hi = r["beta_p025"][name], r["beta_p975"][name]
            mark = "  EXCLUDES 1.0" if (lo > 1.0 or hi < 1.0) else ""
            print(f"      {name:32} {r['beta_mean'][name]:8.4f}  "
                  f"[{lo:7.4f}, {hi:7.4f}]{mark}")
        print()

    print("  Read the intervals, not the top-10. A wider, noisier panel can")
    print("  lower accuracy while improving inference, and inference is what")
    print("  the extra sample was for.\n")

    dest = paths.METRICS / "refit_expanded.json"
    write_json(dest,
               {"repeats": REPEATS, "seed": SEED, "arms": out,
                # No counts restated here. "72 entered unscreened" was true
                # of one OCR run and wrong for every later one; this caveat
                # kept asserting it after the real figure had changed. A
                # caveat that quotes another artefact's number is a copy that
                # cannot be refreshed, so it points instead.
                "caveat": "The expanded panel's added rows are OCR'd: some "
                          "entered unscreened because the OCR lost their "
                          "street, duplicates survive the screen, and ~3% of "
                          "OCR rows merge with a neighbour. The live counts "
                          "are in outputs/metrics/mwpvl_merge.json "
                          "(screenability, internal_duplicates_dropped, "
                          "held_for_clerical_review); they are not restated "
                          "here because a restated count goes stale. A "
                          "percentile interval over re-splits is not a "
                          "standard error and does not account for that "
                          "measurement error.",
                "arm_keys": "Arms are 'original' and 'expanded'. They were "
                            "'original_104' and 'expanded_658' until "
                            "2026-09-15; the counts moved into rows_in_file "
                            "and facilities, which a re-run refreshes and a "
                            "key cannot."})
    print(f"  -> {paths.rel(dest)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
