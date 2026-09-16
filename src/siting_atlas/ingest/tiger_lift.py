"""Does highway access move the choice model? Six specifications, all reported.

    PYTHONPATH=src python -m siting_atlas.ingest.tiger_lift

This is `models/covariate_search.py`'s harness, narrowed to one source.
The measurement rules are copied from it deliberately and not improved
on, because the point of the exercise is a number COMPARABLE to the nine
covariates that have already been tested here:

1  Every arm is a COLUMN SUBSET of one frame. Adding a column with gaps
   drops alternatives, and an arm on its own frame is scored on different
   choice sets. `build_frame` is handed every highway column at once and
   each arm is a view of the result, so the paired difference is about
   the column alone.
2  STRATIFIED BY CHOICE-SET SIZE. Pooled lift across heterogeneous choice
   sets is a Simpson's-paradox trap that has produced two wrong
   conclusions in this project already. A choice set of eleven gives a
   random guess a top-10 hit 91% of the time, so a small-market lift is
   capped near 1.5x whatever the model does.
3  50 PAIRED RE-SPLITS, and the baseline refitted inside each one, so
   every difference reported is a WITHIN-SPLIT difference with a spread
   attached. One split moves a top-10 count by three decisions, which is
   larger than the effect being looked for.

It lives in `ingest/` rather than `models/` only because `models/` is
owned by another agent this week. Nothing in it writes there.

The prior, stated before the result
------------------------------------
Nine covariates have been tested against this baseline and every one
failed; four returned output identical to the baseline to fifteen
decimals, which is what the boundary ``beta -> 0`` looks like from the
outside. Only network proximity has ever landed in the interior. The
base rate for "a new covariate helps" in this project is zero for nine,
and nothing below is tuned until it looks positive: the six
specifications are declared here and all six are reported whatever they
do.

The six, and why each is a different claim
-------------------------------------------
EXTENSIVE, which the model's functional form actually wants:
  ``interchanges``        freeway junctions inside the ZCTA
  ``interstate_miles``    interstate centreline miles inside the ZCTA
  ``primary_road_miles``  the same for all primary roads

INTENSIVE, a workaround for the positivity constraint, and labelled one:
  ``highway_access``      1 / (1 + km to the nearest interchange)
  ``interstate_access``   1 / (1 + km to the nearest interstate)
  ``interchange_decay``   exp(-km to the nearest interchange / 5)

Two decay shapes, not one, because the shape is an assumption and
reporting whichever of the two did better would be choosing the answer.
A seventh arm adds the two best-motivated columns together.
"""

# NOTE ON A DEFECT IN `choice.fit` THAT THIS FILE WORKS AROUND
# ------------------------------------------------------------
# `choice.fit` tries five starts and keeps the best by
# ``best is None or r.fun < best.fun``. The first start is therefore
# accepted unconditionally — including when it returned NaN, because
# every later ``r.fun < nan`` is False and the NaN is never displaced.
# With ``beta = exp(theta)`` an unlucky BFGS excursion overflows theta,
# ``beta'a`` becomes inf, ``inf/inf`` is NaN, and the fit is returned
# looking normal. The first run of this experiment hit it on one arm and
# the only trace was a `nan` in a printed mean.
#
# `models/` is owned by another agent, so the fix is not applied here.
# Instead every split records whether its scores are finite, a
# non-finite split is dropped FROM THAT ARM ONLY, and the count is
# printed and written to the artefact. Silently averaging around it
# would be the actual error.

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor

import numpy as np

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..models.choice import ATTRACTIONS, CBP_ATTRACTIONS
from ..models.choice_runner import SEED, TEST_FRACTION
from ..models.covariate_arms import fit_and_score, split_decisions
from ..models.covariate_frame import build_frame
from ..models.panel_strata import (
    BUCKETS,
    TOP_KS,
    accumulate_strata,
    bucket_of,
    counts_from_sizes,
    finalise,
)
from .tiger_frame import COLUMNS, DECAY_KM, load_frame_inputs
from .tiger_print import print_report

_log = get_logger("ingest.tiger_lift")

REPEATS = 50
BASE = (*ATTRACTIONS, *CBP_ATTRACTIONS)
METRICS = paths.METRICS / "highway_access.json"

#: ``beta`` below this is the boundary in all but name. `choice.py`
#: parameterises ``beta = exp(theta)``, so the optimiser expresses "this
#: column is worthless" by walking theta to minus infinity; it stops
#: wherever the line search gives up, which is a small positive number
#: and not a zero. 1e-6 is six orders of magnitude below the numeraire.
BOUNDARY = 1e-6

__all__ = ["BOUNDARY", "COLUMNS", "run"]

_DATA = None


def _init(data) -> None:
    global _DATA
    _DATA = data


def _repeat(job: tuple[int, dict]) -> dict:
    """One 60/40 re-split of the decisions, every arm refitted on it.

    The baseline is fitted on this same split, so every arm can be
    compared to it WITHIN the split. That pairing is the whole design:
    a fold that happens to hold easy decisions lifts all eight arms
    together and differencing removes it.
    """
    seed, spec = job
    data = _DATA
    tr_idx, te_idx = split_decisions(data.n_decisions, seed, TEST_FRACTION)
    train, test = data.subset(tr_idx), data.subset(te_idx)
    buckets = bucket_of(np.bincount(test.group))
    out = {"seed": seed, "arms": {}}
    scores = {}
    for name, cols in spec.items():
        score, fitted = fit_and_score(train, test, tuple(cols))
        scores[name] = score
        store: dict = {}
        accumulate_strata(store, score, test, buckets)
        out["arms"][name] = {
            "strata": store,
            "mean_prob_of_chosen": float(score[test.chosen].mean()),
            "beta": fitted["beta"],
            "finite": bool(np.isfinite(score).all()),
        }
    base = scores["baseline"]
    for name, score in scores.items():
        # NOT sum(|score|): the scores are probabilities within a choice
        # set, so that sum is the decision count for EVERY arm and the
        # comparison would read 0.0 whatever the column did. The first
        # version of this file made exactly that mistake.
        out["arms"][name]["gap"] = float(np.nanmax(np.abs(score - base)))
    return out


def _merge(repeats: list[dict], name: str, distinct: dict) -> dict:
    """Pool one arm's per-repeat strata and finalise them into lift."""
    total: dict = {}
    for rep in repeats:
        for key, cells in rep["arms"][name]["strata"].items():
            slot = total.setdefault(key, {b: {"n": 0, "hits": 0.0,
                                              "chance": 0.0}
                                          for b, _, _ in BUCKETS})
            for bucket, vals in cells.items():
                for field in ("n", "hits", "chance"):
                    slot[bucket][field] += vals[field]
    return finalise(total, distinct)


def _coefficient(repeats: list[dict], name: str, col: str) -> dict:
    """The added column's coefficient across re-splits, and where it sat.

    Interior or boundary is the question `covariate_search` found matters
    most: a column the optimiser walks to ``beta -> 0`` produces scores
    identical to the baseline's and a lift difference of exactly zero,
    which is a different finding from "it helped a little".
    """
    betas = np.array([r["arms"][name]["beta"][col] for r in repeats])
    return {
        "column": col,
        "beta_median": float(np.median(betas)),
        "beta_p10": float(np.quantile(betas, 0.10)),
        "beta_p90": float(np.quantile(betas, 0.90)),
        "at_boundary_share": float((betas < BOUNDARY).mean()),
        "interior": bool(np.median(betas) >= BOUNDARY),
    }


def _paired(repeats: list[dict], name: str) -> dict:
    """Per-split change in hit rate against the baseline on the same split.

    The marginal effect this experiment is actually asked for. Pooling
    hits over 50 re-splits and dividing gives a lift, and the difference
    of two pooled lifts has no spread attached to it — so a +0.02
    difference and a +2.0 difference read the same way, as a number with
    no scale. The paired per-split difference has a spread: 50 numbers,
    one per split, each the arm's hit rate minus the baseline's hit rate
    on the SAME test decisions.

    The standard error is the plain ``sd / sqrt(50)`` of those
    differences and it is an understatement, deliberately left as one.
    The 50 splits share a single 482-decision frame, so they are not
    independent draws and the true interval is wider. Since almost every
    interval below already covers zero, a correction that widens them
    cannot change a conclusion, and an uncorrected interval that ALREADY
    says "not distinguishable" is the conservative direction to err in.
    """
    out: dict = {}
    for key in (f"top{k}" for k in TOP_KS):
        out[key] = {}
        for bucket, _, _ in BUCKETS:
            diffs = []
            for r in repeats:
                arm = r["arms"][name]["strata"][key][bucket]
                ref = r["arms"]["baseline"]["strata"][key][bucket]
                if ref["n"]:
                    diffs.append(arm["hits"] / arm["n"]
                                 - ref["hits"] / ref["n"])
            d = np.array(diffs) * 100.0
            out[key][bucket] = {
                "mean_pp": float(d.mean()) if len(d) else None,
                "se_pp": float(d.std(ddof=1) / np.sqrt(len(d)))
                if len(d) > 1 else None,
                "share_better": float((d > 0).mean()) if len(d) else None,
                "splits": len(d),
            }
    return out


def _spec() -> dict:
    spec = {"baseline": list(BASE)}
    for col in COLUMNS:
        spec[f"+ {col}"] = [*BASE, col]
    spec["+ interchanges + highway_access"] = [
        *BASE, "interchanges", "highway_access"]
    return spec


def run(workers: int = 5) -> dict:
    facilities, panel, cbp = load_frame_inputs()
    data, coverage = build_frame(facilities, panel, cbp, CBP_ATTRACTIONS,
                                 static=COLUMNS)
    distinct = counts_from_sizes(np.bincount(data.group))
    spec = _spec()

    jobs = [(SEED + r, spec) for r in range(REPEATS)]
    with ProcessPoolExecutor(max_workers=workers, initializer=_init,
                             initargs=(data,)) as pool:
        raw = list(pool.map(_repeat, jobs))

    arms, dropped = {}, {}
    for name, cols in spec.items():
        # A split on which THIS arm failed to converge is dropped from
        # THIS arm and from nothing else; see the note at the top.
        good = [r for r in raw if r["arms"][name]["finite"]]
        if len(good) < len(raw):
            dropped[name] = len(raw) - len(good)
        arms[name] = {
            "columns": list(cols),
            "splits_used": len(good),
            "strata": _merge(good, name, distinct),
            "paired": _paired(good, name),
            "mean_prob_of_chosen": float(np.mean(
                [r["arms"][name]["mean_prob_of_chosen"] for r in good])),
            "max_gap_vs_baseline": float(np.max(
                [r["arms"][name]["gap"] for r in good])),
            "coefficients": [_coefficient(good, name, c)
                             for c in cols if c not in BASE],
        }
    report = {"seed": SEED, "repeats": REPEATS, "boundary": BOUNDARY,
              "test_fraction": TEST_FRACTION, "decay_km": DECAY_KM,
              "coverage": coverage, "distinct_by_stratum": distinct,
              "non_finite_fits": dropped, "arms": arms}
    print_report(report)
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    write_json(METRICS, report)
    print(f"\n  -> {paths.rel(METRICS)}\n")
    return report


def main() -> int:
    paths.ensure_dirs()
    init_run()
    configure()
    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
