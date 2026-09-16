"""The decisive covariate-leakage test: refit on strictly pre-opening CBP.

    PYTHONPATH=src .venv/bin/python -m siting_atlas.models.leakage_decisive

WHAT THE ABLATION COULD NOT DO
------------------------------
``models/leakage_test`` removed ``warehousing_establishments`` and measured
what was left: 7.70 of 38 top-10 hits, winning 50 of 50 paired re-splits. It
established that the covariate is load-bearing and it explicitly could not
establish why, because self-counting and genuine agglomeration make the same
prediction. Warehouses cluster near warehouses whether or not this warehouse
is in the count.

The one thing that separates them is a CBP vintage measured strictly before
the building existed. The guard in ``ingest/cbp_detail.vintage_for`` aims at
that and misses, because it is calibrated on ``open_year``, which is the
quarter of the earliest OSHA inspection -- an upper bound running a median 34
months late. MWPVL states opening months outright, so for the buildings that
appear in both sources the true date is available and the vintage can be
chosen against it instead.

THREE ARMS, ONE SET OF DECISIONS
--------------------------------
  osha_bound     vintage chosen off `open_year`, the status quo
  true_date      vintage chosen off the MWPVL-stated opening year
  no_covariate   warehousing removed entirely, the floor

Requiring a clean vintage DROPS facilities: the earliest comparable CBP
vintage is 2017, so a building that truly opened in 2017 or earlier has none,
and a building MWPVL does not list has no true date at all. If ``true_date``
were fitted on fewer decisions than ``osha_bound`` the comparison would
confound leakage with sample size, so all three arms are restricted to the
INTERSECTION -- the decisions every arm can fit -- and the loss is reported
rather than absorbed.

WHAT A DIFFERENCE BETWEEN THE FIRST TWO ARMS DOES NOT MEAN
----------------------------------------------------------
``true_date`` reads an OLDER vintage, not merely a cleaner one. Removing the
leak and adding two years of staleness are the SAME intervention here and no
choice of vintage separates them, so a drop is an upper bound on the leak and
not a measurement of it. ``leakage_dates.self_count_delta`` attacks that
ambiguity from the other side, without fitting anything: it asks whether the
chosen ZCTA gains about one more establishment than the average alternative
in its own metro, which is what self-counting looks like and drift does not.

Percentile intervals over re-splits are NOT standard errors. They describe
the spread of the estimator across partitions of one fixed, small sample.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common import paths
from ..common.log_json import write_json
from ..warehouse.mwpvl_merge import DELIVERY_STATION_TABLES
from ..warehouse.national import load_national
from . import leakage_print
from .choice import ATTRACTIONS, CBP_ATTRACTIONS, build, evaluate, fit
from .choice_runner import SEED, TEST_FRACTION
from .leakage_dates import (
    provenance,
    self_count_delta,
    true_open_years,
)

#: As the ablation and the GBM benchmark, so the three are comparable. A
#: single split of a 12-decision test set decides nothing.
REPEATS = 50

#: The covariate under suspicion.
COLUMN = CBP_ATTRACTIONS[0]

#: Above this the optimiser has run beta to the boundary rather than found an
#: interior maximum: the covariate separated that split's choice sets and the
#: likelihood is flat above it. Counted and reported, never discarded.
DIVERGED = 1e6


def _load():
    cbp_path = paths.INTERIM / "cbp_detail.parquet"
    if not cbp_path.exists():
        raise SystemExit(
            f"\n  {paths.rel(cbp_path)} absent, so there is no warehousing\n"
            "  covariate to test. Run:\n"
            "      python -m siting_atlas.ingest.cbp_detail\n")
    facilities = load_national()
    panel = pd.read_parquet(paths.PANEL,
                            columns=["zcta", "cbsa_code", *ATTRACTIONS])
    return facilities, panel, pd.read_parquet(cbp_path)


def _dated(facilities: pd.DataFrame, true_year: dict[str, int]):
    """The panel with ``open_year`` REPLACED by the stated opening year.

    Substituting the column rather than adding one is deliberate: the vintage
    choice inside ``choice.build`` is then untouched, so the two CBP arms run
    the same code over the same guard and differ in the date and nothing
    else. A facility with no stated date gets NaN and ``build`` drops it, the
    same way it drops a facility with no clean vintage.
    """
    out = facilities.copy()
    out["open_year"] = out["facility_id"].astype(str).map(true_year)
    return out


def _arms(facilities, panel, cbp, true_year) -> dict:
    """The three arms, all restricted to the decisions all three can fit."""
    def make(f, f_true):
        return {"osha_bound": build(f, panel, cbp, CBP_ATTRACTIONS),
                "true_date": build(f_true, panel, cbp, CBP_ATTRACTIONS),
                "no_covariate": build(f, panel, None, ())}

    wide = make(facilities, _dated(facilities, true_year))
    keep = sorted(set.intersection(*(set(d.ids) for d in wide.values())))
    ids = facilities["facility_id"].astype(str)
    sub = facilities[ids.isin(keep)]
    arms = make(sub, _dated(sub, true_year))
    # The arms must be the same decisions in the same order or the paired
    # differences below are pairing different buildings.
    first = arms["osha_bound"].ids
    for name, data in arms.items():
        if data.ids != first:
            raise AssertionError(f"{name} holds a different decision set")
    return arms, wide, keep


def _measure(data, repeats: int = REPEATS) -> dict:
    """Refit inside every split. Top-10 as HITS, plus the beta that made it."""
    hits, nulls, briers, betas = [], [], [], []
    n_test = int(round(data.n_decisions * TEST_FRACTION))
    for r in range(repeats):
        rng = np.random.default_rng(SEED + r)
        order = rng.permutation(data.n_decisions)
        cut = int(round(data.n_decisions * (1 - TEST_FRACTION)))
        fitted = fit(data.subset(np.sort(order[:cut])))
        theta = np.asarray(fitted["theta"], float)
        out = evaluate(theta, data.subset(np.sort(order[cut:])))
        hits.append(out["top10"] * out["n_decisions"])
        nulls.append(out["top10_uniform"] * out["n_decisions"])
        briers.append(out["brier"])
        betas.append(fitted["beta"].get(COLUMN, float("nan")))
    hits = np.array(hits, float)
    beta = np.array(betas, float)
    summary = {
        "covariates": list(data.names),
        "n_decisions": int(data.n_decisions),
        "n_test": n_test,
        "top10_hits_mean": float(hits.mean()),
        "top10_hits_sd": float(hits.std(ddof=1)),
        "top10_rate": float(hits.mean() / n_test),
        "uniform_null_hits": float(np.mean(nulls)),
        "lift_over_own_null": float(hits.mean() / np.mean(nulls)),
        "brier_mean": float(np.mean(briers)),
        "hits": hits.tolist(),
    }
    if not np.all(np.isnan(beta)):
        # The MEDIAN, not the mean: a split where beta runs to the boundary
        # returns 1e15 and would carry the mean with it.
        summary[f"beta_{COLUMN}"] = {
            "median": float(np.nanmedian(beta)),
            "p2_5": float(np.nanpercentile(beta, 2.5)),
            "p97_5": float(np.nanpercentile(beta, 97.5)),
            "splits_at_boundary": int((beta > DIVERGED).sum()),
            "units": "ratio to one household, on the mean-scaled column",
        }
    return summary


def _paired(a: dict, b: dict) -> dict:
    """a minus b, split by split. The arms share splits, so this is paired."""
    d = np.array(a["hits"]) - np.array(b["hits"])
    return {
        "mean_difference_hits": float(d.mean()),
        "sd_of_difference": float(d.std(ddof=1)),
        "first_wins": int((d > 0).sum()),
        "ties": int((d == 0).sum()),
        "second_wins": int((d < 0).sum()),
    }


def _sensitivity(facilities, panel, cbp, dates) -> dict:
    """The same test on dates from the two DELIVERY STATION tables only.

    The headline set takes a stated date wherever the address matches, so half
    of it comes from a table for a different facility class. This arm refuses
    those: the cleaner sample and the much smaller one. At six held-out
    decisions it settles nothing, and is here so the headline is not the only
    number on the page.
    """
    ds = dates[dates["mwpvl_table"].isin(DELIVERY_STATION_TABLES)]
    year = dict(zip(ds["facility_id"], ds["true_open_year"], strict=True))
    arms, _, keep = _arms(facilities, panel, cbp, year)
    measured = {k: _measure(v) for k, v in arms.items()}
    return {
        "n_decisions": len(keep),
        "top10_hits": {k: v["top10_hits_mean"] for k, v in measured.items()},
        "paired_osha_minus_true": _paired(measured["osha_bound"],
                                          measured["true_date"]),
    }


def _self_count(delta: pd.DataFrame) -> dict:
    """Summarise the model-free self-count check. Nothing is tested here."""
    alts = float(delta["n_alternatives"].sum())
    return {
        "n_facilities": int(len(delta)),
        "chosen_delta_mean": float(delta["chosen_delta"].mean()),
        "peer_mean_delta_mean": float(delta["peer_mean_delta"].mean()),
        "excess_mean": float(delta["excess"].mean()),
        "excess_median": float(delta["excess"].median()),
        "excess_sd": float(delta["excess"].std(ddof=1)),
        "chosen_gains_at_least_one": int((delta["chosen_delta"] >= 1).sum()),
        "vintage_unchanged": int((delta["v_true"] == delta["v_osha"]).sum()),
        # The two column means `choice.build` divides by, so the arms'
        # coefficients can be compared in raw units if wanted.
        "column_mean_true_vintage": float(delta["alt_total_true"].sum()/alts),
        "column_mean_osha_vintage": float(delta["alt_total_osha"].sum()/alts),
    }


def main() -> int:
    facilities, panel, cbp = _load()
    dates = true_open_years()
    year = dict(zip(dates["facility_id"], dates["true_open_year"],
                    strict=True))
    arms, wide, keep = _arms(facilities, panel, cbp, year)
    measured = {k: _measure(v) for k, v in arms.items()}
    self_count = _self_count(self_count_delta(
        facilities[facilities["facility_id"].astype(str).isin(keep)],
        panel, cbp, year, ATTRACTIONS, COLUMN))

    pairs = {
        "osha_bound_minus_true_date": _paired(measured["osha_bound"],
                                              measured["true_date"]),
        "true_date_minus_no_covariate": _paired(measured["true_date"],
                                                measured["no_covariate"]),
        "osha_bound_minus_no_covariate": _paired(measured["osha_bound"],
                                                 measured["no_covariate"]),
    }
    retained = (pairs["true_date_minus_no_covariate"]["mean_difference_hits"]
                / pairs["osha_bound_minus_no_covariate"]
                ["mean_difference_hits"])
    prov = provenance(dates, keep, facilities)
    wide_n = int(wide["osha_bound"].n_decisions)

    report = {
        "repeats": REPEATS, "seed": SEED, "test_fraction": TEST_FRACTION,
        "n_decisions_intersection": len(keep),
        "n_decisions_osha_bound_unrestricted": wide_n,
        "n_decisions_no_covariate_unrestricted":
            int(wide["no_covariate"].n_decisions),
        "n_decisions_lost": wide_n - len(keep),
        "arms": measured,
        "paired_differences": pairs,
        "share_of_covariate_value_retained": float(retained),
        # `choice.build` divides every column by its own mean and the two arms
        # read a vintage whose warehousing mean differs, so the scaled betas
        # are not one unit. Dividing each by its own column mean puts both on
        # the raw column; the households scale they are ratios to is identical
        # across arms, so this ratio compares the per-establishment weight.
        "beta_per_establishment_osha_over_true": float(
            (measured["osha_bound"][f"beta_{COLUMN}"]["median"]
             / self_count["column_mean_osha_vintage"])
            / (measured["true_date"][f"beta_{COLUMN}"]["median"]
               / self_count["column_mean_true_vintage"])),
        "true_date_provenance": prov,
        "self_count_check": self_count,
        "delivery_station_tables_only": _sensitivity(facilities, panel, cbp,
                                                     dates),
        "caveats": [
            "A percentile interval over re-splits is NOT a standard error. "
            "It describes the spread of the estimator over partitions of one "
            f"fixed sample of {len(keep)} decisions.",
            "true_date reads an OLDER vintage as well as a cleaner one. "
            "Removing the leak and adding staleness are the same "
            "intervention, so the osha_bound - true_date gap is an UPPER "
            "BOUND on the leak, not a measurement of it.",
            f"The intersection is not a random subsample of the {wide_n}: it "
            "is the buildings MWPVL happens to list and the address matcher "
            "happens to reach, and it is easier than the full panel.",
            "Nothing was corrected. "
            f"{prov['stated_date_not_earlier_than_the_bound']} stated date(s) "
            "are NOT earlier than the OSHA bound for the same building, and "
            "are used as stated.",
        ],
    }
    leakage_print.render(report)
    out = paths.METRICS / "leakage_decisive.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, report)
    print(f"  -> {paths.rel(out)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
