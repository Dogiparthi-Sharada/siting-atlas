"""Fit the conditional ZCTA-choice model and report it honestly.

    python -m siting_atlas.models.choice_runner

Why the national frame and not the pilot
----------------------------------------
The pilot panel has 19 of 43 opening quarters filled in by convention
(44.2%), and `docs/MODEL_SPEC.md` refused to fit over that. The national
frame has 104 of 104 (100%), so the objection does not apply to it. Going
national is not only a power decision, it is what removes the blocker.

    pilot      24/43 quarters reported, 28 independent episodes
    national  104/104 reported,         79 independent episodes

The split is over DECISIONS, never over alternatives. Splitting alternatives
would put a metro's ZCTAs on both sides of the line and leak the answer.
"""

from __future__ import annotations

import textwrap

import numpy as np
import pandas as pd

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer
from ..warehouse.national import load_national
from .choice import ATTRACTIONS, CBP_ATTRACTIONS, build, evaluate, fit
from .choice_conformal import calibrate, summarise
from .choice_inference import summarise as summarise_inference

_log = get_logger("models.choice_runner")

#: Deterministic. The split decides the headline, so an unseeded shuffle
#: would make the reported number irreproducible.
SEED = 20260914

#: Fraction of DECISIONS held out. 40% of 79 is ~32 held-out decisions, which
#: is thin but is the point: the alternative is reporting an in-sample fit.
TEST_FRACTION = 0.40

#: Three-way split when conformal sets are wanted: the calibration
#: decisions must be disjoint from BOTH the fit and the evaluation or the
#: coverage guarantee is void. 50/25/25 rather than a thinner calibration
#: slice because q_hat is an order statistic -- at n=23 it is the 22nd of
#: 23, so every extra decision visibly tightens it.
CONFORMAL_SPLIT = (0.50, 0.25)

#: Reported at three levels on purpose. One number hides the trade; three
#: show the reader exactly what certainty costs in ZIP codes.
CONFORMAL_ALPHAS = (0.10, 0.20, 0.30)


def _benchmark(d, test_idx, column: str) -> dict:
    """Rank by ONE raw covariate, no fitting, no parameters.

    If a single raw column matches the estimated model, the estimation bought
    nothing, and that is a finding either way. Harsher than a gradient-boosted
    ranker because it cannot be accused of overfitting the test decisions: it
    has nothing to overfit with.
    """
    te = d.subset(test_idx)
    v = te.a[:, te.names.index(column)]
    totals = np.bincount(te.group, weights=v)
    with np.errstate(invalid="ignore", divide="ignore"):
        p = np.where(totals[te.group] > 0, v / totals[te.group], 0.0)
    hits = {}
    for k in (1, 5, 10):
        n = 0
        for g in range(te.n_decisions):
            rows = np.flatnonzero(te.group == g)
            order = rows[np.argsort(-p[rows])]
            n += int(te.chosen[g] in order[:k])
        hits[f"top{k}"] = n / te.n_decisions
    y = np.zeros(len(p))
    y[te.chosen] = 1.0
    hits["brier"] = float(np.mean((p - y) ** 2))
    return hits


def _print_inference(inf: dict) -> None:
    """The interval table. Every row is a RATIO, and it says so twice.

    A coefficient here is "worth this many households", so the number to
    compare against is 1.0 and not 0.0. No zero test is printed at all.
    """
    print(f"\n  UNCERTAINTY   {inf['replicates']} bootstrap replicates over "
          f"{inf['n_decisions']} DECISIONS, seed {inf['seed']}")
    print("  Every interval is a RATIO TO ONE HOUSEHOLD (households is the "
          "numeraire).\n  The null that matters is 1.0, not 0.0.\n")
    print(f"    {'covariate':28}{'beta':>8}{'95% percentile':>22}"
          f"{'excludes 1.0':>14}")
    for name, p in inf["parameters"].items():
        ci = p["bootstrap_over_decisions"]
        span = (f"one-sided, < {ci['upper']:.3f}" if p["at_boundary"]
                else f"{ci['lower']:.3f} to {ci['upper']:.3f}")
        verdict = "YES" if ci["excludes_ratio_one"] else "no"
        if p["at_boundary"] and ci["excludes_ratio_one"]:
            verdict = "YES, below"
        print(f"    {name:28}{p['beta_point']:>8.4f}{span:>22}{verdict:>14}")

    print(f"\n    metro-clustered - the {inf['n_decisions']} decisions sit in "
          f"only {inf['n_metros']} metros and\n    decisions in one metro "
          f"share a choice set. The conservative version.")
    for name, p in inf["parameters"].items():
        ci = p["bootstrap_over_metros"]
        span = (f"one-sided, < {ci['upper']:.3f}" if p["at_boundary"]
                else f"{ci['lower']:.3f} to {ci['upper']:.3f}")
        print(f"    {name:28}{'':>8}{span:>22}"
              f"{'YES' if ci['excludes_ratio_one'] else 'no':>14}")

    print("\n    BCa, interior parameters only (bias correction and a "
          "jackknife\n    acceleration over the same decisions)")
    for name, p in inf["parameters"].items():
        b = p["bca"]
        if not b.get("available", True):
            print(f"    {name:28}{'':>8}{'refused at boundary':>22}{'--':>14}")
            continue
        span = f"{b['lower']:.3f} to {b['upper']:.3f}"
        print(f"    {name:28}{'':>8}{span:>22}"
              f"{'YES' if b['excludes_ratio_one'] else 'no':>14}")

    print("\n  SANDWICH  (Train Sec. 8.6 p.201), INTERIOR parameters only")
    for name, s in inf["sandwich"].items():
        if s["available"]:
            print(f"    {name:28}{s['lower']:.3f} to {s['upper']:.3f}   "
                  f"z against 1.0 = {s['z_against_ratio_one']:.2f}   "
                  f"p = {s['p_two_sided_against_ratio_one']:.3f}")
        else:
            print(f"    {name:28}REFUSED - beta is at the boundary, so the "
                  f"optimum is not interior,\n    {'':28}the Hessian is not "
                  f"the information matrix the asymptotics\n    {'':28}"
                  f"assume, and a number here would mean nothing.")
    print()
    for line in textwrap.wrap(inf["train_precondition"], 74):
        print(f"  {line}")


def run() -> dict:
    """Fit, hold out, evaluate, benchmark. Returns everything measured."""
    with traced_layer("L5", "conditional ZCTA choice"):
        with step("choice:load"):
            facilities = load_national()
            panel = pd.read_parquet(
                paths.PANEL,
                columns=["zcta", "cbsa_code", *ATTRACTIONS])
            cbp_path = paths.INTERIM / "cbp_detail.parquet"
            cbp = pd.read_parquet(cbp_path) if cbp_path.exists() else None
            if cbp is None:
                _log.warning("no %s - fitting without the warehousing "
                             "covariate, which is the one that works. Run "
                             "python -m siting_atlas.ingest.cbp_detail",
                             paths.rel(cbp_path))
            data = build(facilities, panel, cbp,
                         CBP_ATTRACTIONS if cbp is not None else ())
            metric("choice_decisions", data.n_decisions)

        with step("choice:split"):
            rng = np.random.default_rng(SEED)
            order = rng.permutation(data.n_decisions)
            cut = int(round(data.n_decisions * (1 - TEST_FRACTION)))
            train_idx, test_idx = np.sort(order[:cut]), np.sort(order[cut:])
            train, test = data.subset(train_idx), data.subset(test_idx)

        with step("choice:fit"):
            fitted = fit(train)
            metric("choice_rho_squared", fitted["mcfadden_rho_squared"])

        with step("choice:inference"):
            # On the TRAINING decisions, because that is the sample the
            # published beta was estimated on and an interval must describe
            # the estimator that produced the point estimate beside it.
            inference = summarise_inference(train, fitted, SEED)
            w = inference["parameters"].get("warehousing_establishments")
            if w is not None:
                metric("choice_warehousing_ratio_excludes_one",
                       float(w["bootstrap_over_decisions"]
                             .get("excludes_ratio_one", False)))

        with step("choice:conformal"):
            i1 = int(data.n_decisions * CONFORMAL_SPLIT[0])
            i2 = int(data.n_decisions * sum(CONFORMAL_SPLIT))
            c_tr = np.sort(order[:i1])
            c_cal = np.sort(order[i1:i2])
            c_te = np.sort(order[i2:])
            c_fit = fit(data.subset(c_tr))
            c_theta = np.asarray(c_fit["theta"], float)
            conformal = {}
            for a in CONFORMAL_ALPHAS:
                q = calibrate(c_theta, data.subset(c_cal), a)
                conformal[f"alpha_{a:.2f}"] = summarise(
                    c_theta, data.subset(c_te), q, a)
            conformal["split"] = {"train": len(c_tr), "calibrate": len(c_cal),
                                  "test": len(c_te)}

        with step("choice:evaluate"):
            theta = np.asarray(fitted["theta"], float)
            in_sample = evaluate(theta, train)
            held_out = evaluate(theta, test)
            bench = {c: _benchmark(data, test_idx, c)
                     for c in data.names}

    report = {
        "frame": "national",
        "n_decisions_total": data.n_decisions,
        "n_train_decisions": int(len(train_idx)),
        "n_test_decisions": int(len(test_idx)),
        "seed": SEED,
        "fit": fitted,
        "inference": inference,
        "in_sample": in_sample,
        "held_out": held_out,
        "benchmarks_single_covariate": bench,
        "conformal": conformal,
        "attractions": list(data.names),
        "reporting_rule": (
            "Raw Brier PAIR and top-k against a uniform-within-choice-set "
            "null. Never a skill score: Gneiting & Raftery (2007) Sec. 2.3 "
            "p.362 shows skill scores are generally improper even when the "
            "underlying score is proper."),
    }
    out = paths.METRICS / "choice_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, report)
    artefact(out, decisions=data.n_decisions)
    return report


def main() -> int:
    paths.ensure_dirs()
    init_run()
    configure()
    r = run()
    f, h, b = r["fit"], r["held_out"], r["benchmarks_single_covariate"]

    print(f"\n  CONDITIONAL ZCTA CHOICE - {r['frame']} frame")
    print(f"  {r['n_decisions_total']} decisions "
          f"({r['n_train_decisions']} train / {r['n_test_decisions']} test), "
          f"{f['n_parameters']} free parameters")
    print(f"  events per parameter "
          f"{r['n_train_decisions'] / max(f['n_parameters'], 1):.1f} "
          f"against a floor of 10\n")

    print("  COEFFICIENTS  (households is the numeraire, fixed at 1.000)")
    for k, v in f["beta"].items():
        print(f"    {k:22} {v:10.4f}")
    print(f"\n  McFadden rho-squared {f['mcfadden_rho_squared']:.4f}   "
          f"converged={f['converged']}")

    _print_inference(r["inference"])

    print("\n  HELD OUT, against a uniform-within-metro null")
    print(f"    {'':22}{'model':>12}{'null':>12}")
    for label, a, bb in (
            ("Brier", h["brier"], h["brier_uniform_null"]),
            ("P(chosen ZCTA)", h["mean_prob_of_chosen"],
             h["mean_prob_uniform"]),
            ("top-1 hit rate", h["top1"], h["top1_uniform"]),
            ("top-5 hit rate", h["top5"], h["top5_uniform"]),
            ("top-10 hit rate", h["top10"], h["top10_uniform"])):
        print(f"    {label:22}{a:12.4f}{bb:12.4f}")

    n = r["n_test_decisions"]
    print(f"\n  BENCHMARKS - rank by ONE raw covariate, nothing fitted"
          f"   (hits of {n})")
    print(f"    {'':30}{'top-1':>8}{'top-5':>8}{'top-10':>8}")
    print(f"    {'MODEL (all covariates)':30}{h['top1']*n:>8.0f}"
          f"{h['top5']*n:>8.0f}{h['top10']*n:>8.0f}")
    for col, hits in b.items():
        print(f"    {col:30}{hits['top1']*n:>8.0f}"
              f"{hits['top5']*n:>8.0f}{hits['top10']*n:>8.0f}")
    print(f"    {'random (uniform in metro)':30}"
          f"{h['top1_uniform']*n:>8.0f}{h['top5_uniform']*n:>8.0f}"
          f"{h['top10_uniform']*n:>8.0f}")
    print("\n  If a single raw covariate matches the model, the estimation "
          "bought nothing.\n  That is a finding either way.")

    c = r["conformal"]
    sp = c["split"]
    print(f"\n  CONFORMAL PREDICTION SETS   ({sp['train']} fit / "
          f"{sp['calibrate']} calibrate / {sp['test']} test)")
    print(f"    {'target':>8}{'achieved':>10}{'ZIPs in set':>14}"
          f"{'as % of metro':>16}")
    for a in CONFORMAL_ALPHAS:
        s_ = c[f"alpha_{a:.2f}"]
        print(f"    {1 - a:>7.0%}{s_['empirical_coverage']:>10.1%}"
              f"{s_['set_size_median']:>14.0f}"
              f"{s_['median_share_of_choice_set']:>15.0%}")
    print("    Coverage is guaranteed whatever the model does; the SET SIZE "
          "is\n    where a weak model pays. Read the last column as how much "
          "of a\n    metro a city would still have to examine.")
    print(f"\n  -> {paths.rel(paths.METRICS / 'choice_report.json')}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
