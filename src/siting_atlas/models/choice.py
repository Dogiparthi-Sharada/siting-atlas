"""Conditional ZCTA-choice model: which ZIP, given a station opens.

The estimand, in one sentence
----------------------------
Given that one delivery station opens in metro ``m``, which ZCTA of ``m`` is
it sited in? That is a choice among mutually exclusive alternatives made by a
single decision maker, which the retired hazard model was not — see
`docs/MODEL_SPEC.md` and `docs/METHODS_RESEARCH.md` section 14.2.

Why this one fits and the hazard model did not
----------------------------------------------
The hazard model broke Train (2009) section 3.7.1, p. 61: the likelihood
assumes "each decision maker's choice is independent of that of other
decision makers", and one station switching on 58 ZCTAs at once is one draw
counted 58 times. Here each opening contributes exactly one term to the
log-likelihood, so the count of terms is the count of decisions.

The functional form is forced, not chosen
-----------------------------------------
Train section 3.4, Example 2 (printed p. 54): zone boundaries are the
researcher's arbitrary choice, and a model that is not invariant to them is
measuring the Census. Invariance requires ``exp(V)`` to be additive across a
merger of zones, which holds when ``V_j = ln(beta' a_j)`` and the attraction
variables ``a`` are EXTENSIVE - counts that genuinely add. Households, land
area and establishments qualify. Medians, rates and densities do not: the
median income of two merged ZIPs is not the sum of the two medians.

That form collapses the logit to something simpler than a logit:

    P(j | m) = exp(V_j) / sum_k exp(V_k) = (beta' a_j) / sum_k (beta' a_k)

No exponentials at all. The probability a ZCTA is chosen is just its share of
the metro's total attraction.

Two consequences the specification did not anticipate
-----------------------------------------------------
1. **The model is scale-invariant in beta.** Multiplying every coefficient by
   c leaves every probability unchanged, so only RATIOS are identified. One
   coefficient must be normalised. We fix households at 1, making the others
   "worth this many households". `MODEL_SPEC.md` counts three parameters; only
   TWO are estimable, which improves events-per-parameter rather than harming
   it.
2. **beta' a must be positive** for every alternative or the probability is
   undefined. We parameterise ``beta_k = exp(theta_k)``, which enforces it and
   restricts every attraction variable to be weakly attractive. That is a real
   restriction and it is reported, not hidden: a variable that genuinely
   repels cannot be expressed here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from ..common.logging_setup import get_logger
from .accessibility import COLUMN as SAVING_COLUMN
from .accessibility import savings_for_metro

_log = get_logger("models.choice")

#: Extensive counts only. See the module docstring: intensive variables
#: (medians, rates, densities) break the aggregation invariance that is the
#: whole reason for the ln(beta'a) form.
ATTRACTIONS = ("households", "land_area_sqmi", "establishments")

#: Households is the numeraire. Scale invariance means one coefficient is
#: free to choose; fixing the largest and most complete one keeps the other
#: two interpretable as "worth this many households".
NUMERAIRE = "households"

#: Industry counts from CBP, added per decision on a LAGGED vintage.
#: Extensive, so they may sit inside the log with the rest. See
#: `ingest/cbp_detail.py` for why the lag is not optional.
CBP_ATTRACTIONS = ("warehousing_establishments",)

#: Computed per decision from the network that already existed, so it
#: cannot be joined from a table. NOT extensive - see accessibility.py.
SAVING_ATTRACTIONS = (SAVING_COLUMN,)

__all__ = ["ATTRACTIONS", "ChoiceData", "build", "fit", "predict", "evaluate"]


class ChoiceData:
    """Choice sets and the chosen alternative, one record per decision.

    Held as flat arrays with a group index rather than a list of frames: the
    likelihood is a couple of ``np.bincount`` calls that way, and at 25,000
    alternatives the frame-per-decision version spends all its time in pandas.
    """

    def __init__(self, attractions: np.ndarray, group: np.ndarray,
                 chosen: np.ndarray, decision_ids: list[str],
                 names: tuple[str, ...] = ATTRACTIONS):
        self.a = attractions          # (n_alternatives, n_attractions)
        self.group = group            # (n_alternatives,) decision index
        self.chosen = chosen          # (n_decisions,) row index of the choice
        self.ids = decision_ids
        self.names = tuple(names)     # column order, for labelling beta
        self.n_decisions = len(decision_ids)

    def subset(self, keep: np.ndarray) -> ChoiceData:
        """The data restricted to a subset of DECISIONS, reindexed."""
        mask = np.isin(self.group, keep)
        remap = dict(zip(keep, range(len(keep)), strict=True))
        rows = np.flatnonzero(mask)
        row_remap = dict(zip(rows, range(len(rows)), strict=True))
        return ChoiceData(
            self.a[mask],
            np.array([remap[g] for g in self.group[mask]]),
            np.array([row_remap[self.chosen[g]] for g in keep]),
            [self.ids[g] for g in keep], self.names)


def build(facilities: pd.DataFrame, panel: pd.DataFrame,
          cbp_detail: pd.DataFrame | None = None,
          extra: tuple[str, ...] = (),
          with_saving: bool = False) -> ChoiceData:
    """Assemble choice sets: alternatives are the ZCTAs of the chosen metro.

    A facility whose own ZCTA is absent from the panel is dropped rather than
    given a choice set that excludes the option it actually took — a choice
    set that does not contain the observed choice has zero likelihood and
    would silently poison the fit.

    ``cbp_detail`` adds industry counts that are LAGGED PER DECISION. An
    Amazon delivery station is itself a warehousing establishment, so scoring
    a 2019 opening on 2022 warehousing counts would let the covariate contain
    the outcome. Each facility is instead scored on the latest CBP vintage
    strictly earlier than its own opening year, and a facility with no such
    vintage is dropped rather than scored on a contemporaneous one.
    """
    columns = list(ATTRACTIONS) + [c for c in extra if c not in ATTRACTIONS]
    if with_saving:
        columns.append(SAVING_COLUMN)
    geo = ["latitude", "longitude"] if with_saving else []
    zctas = panel.drop_duplicates("zcta")[
        ["zcta", "cbsa_code", *ATTRACTIONS, *geo]].dropna(
        subset=["cbsa_code", *geo])
    for col in ATTRACTIONS:
        zctas = zctas[zctas[col].notna() & (zctas[col] > 0)]

    lagged: dict[int, pd.DataFrame] = {}
    vintages: list[int] = []
    if cbp_detail is not None and extra:
        vintages = sorted(cbp_detail["cbp_year"].unique().tolist())
        for year in vintages:
            slice_ = cbp_detail.loc[cbp_detail["cbp_year"] == year,
                                    ["zcta", *extra]]
            merged = zctas.merge(slice_, on="zcta", how="left")
            # A ZIP absent from CBP for an industry has zero establishments,
            # not an unknown number. Treating it as missing would drop the
            # residential ZIPs this covariate exists to distinguish.
            for col in extra:
                merged[col] = merged[col].fillna(0.0)
            lagged[year] = merged

    by_cbsa = dict(iter(zctas.groupby("cbsa_code")))
    lagged_by_cbsa = {y: dict(iter(f.groupby("cbsa_code")))
                      for y, f in lagged.items()}
    home = zctas.set_index("zcta")["cbsa_code"].to_dict()

    prior_zctas_by_facility: dict[str, list[str]] = {}
    if with_saving:
        fac_years = pd.to_numeric(facilities.get("open_year"), errors="coerce")
        fac_cbsa = facilities["zcta"].astype(str).str.strip().map(home)
        for idx, row in facilities.iterrows():
            y, c = fac_years.get(idx), fac_cbsa.get(idx)
            if pd.isna(y) or c is None:
                continue
            earlier = facilities[(fac_cbsa == c) & (fac_years < y)]
            prior_zctas_by_facility[str(row.get("facility_id"))] = (
                earlier["zcta"].astype(str).str.strip().tolist())

    a_blocks, groups, chosen, ids = [], [], [], []
    offset, dropped, no_vintage = 0, 0, 0
    for _, fac in facilities.iterrows():
        z = str(fac.get("zcta") or "").strip()
        cbsa = home.get(z)
        if cbsa is None or cbsa not in by_cbsa:
            dropped += 1
            continue

        alts = by_cbsa[cbsa]
        if extra:
            try:
                open_year = int(float(fac.get("open_year")))
            except (TypeError, ValueError):
                no_vintage += 1
                continue
            earlier = [y for y in vintages if y < open_year]
            if not earlier:
                no_vintage += 1
                continue
            alts = lagged_by_cbsa[max(earlier)][cbsa]

        where = np.flatnonzero(alts["zcta"].to_numpy() == z)
        if not len(where):
            dropped += 1
            continue

        block = alts[columns[:-1]] if with_saving else alts[columns]
        block = block.to_numpy(float)
        if with_saving:
            # The network that existed WHEN THIS DECISION WAS MADE: other
            # Amazon facilities in the same metro with an earlier opening
            # year. Real locations, not a solved optimum, so the covariate
            # cannot be our own cost model predicting itself.
            key = str(fac.get("facility_id"))
            prior = prior_zctas_by_facility.get(key, [])
            saving = savings_for_metro(alts, prior)
            block = np.column_stack([block, saving])
        a_blocks.append(block)
        groups.append(np.full(len(alts), len(ids)))
        chosen.append(offset + int(where[0]))
        ids.append(str(fac.get("facility_id") or len(ids)))
        offset += len(alts)

    if no_vintage:
        _log.warning("%d facility(ies) dropped: no CBP vintage strictly "
                     "earlier than the opening year, so any industry "
                     "covariate would risk containing the outcome",
                     no_vintage)

    if dropped:
        _log.warning("%d facility(ies) dropped: no panel ZCTA, or the chosen "
                     "ZCTA is absent from its own metro's choice set", dropped)
    if not a_blocks:
        raise ValueError("no usable decisions - check the zcta join")

    a = np.vstack(a_blocks)
    # Scale each column by its mean so the optimiser sees O(1) numbers. This
    # changes the units of beta and nothing else: the probabilities are a
    # ratio, so a common rescale of a column cancels between the numerator
    # and the sum. Recorded in the artefact so beta can be un-scaled.
    scale = a.mean(axis=0)
    sizes = np.bincount(np.concatenate(groups))
    _log.info("%d decisions, %d alternatives, median choice set %d",
              len(ids), len(a), int(np.median(sizes)))
    return ChoiceData(a / scale, np.concatenate(groups),
                      np.array(chosen), ids, tuple(columns))


def _probabilities(theta: np.ndarray, d: ChoiceData) -> np.ndarray:
    """P(j | m) for every alternative, under beta_numeraire == 1."""
    beta = np.concatenate([[1.0], np.exp(theta)])
    util = d.a @ beta                      # = beta' a_j, strictly positive
    totals = np.bincount(d.group, weights=util)
    return util / totals[d.group]


def _neg_log_likelihood(theta: np.ndarray, d: ChoiceData) -> float:
    p = _probabilities(theta, d)
    return -float(np.log(np.maximum(p[d.chosen], 1e-300)).sum())


def fit(d: ChoiceData, seed: int = 20260914) -> dict:
    """Maximum likelihood, with the numeraire fixed and beta > 0 enforced.

    `theta` is log-beta for the non-numeraire attractions, so the optimiser is
    unconstrained while beta stays positive. Nelder-Mead after BFGS because at
    two parameters it costs nothing and guards against a bad gradient at the
    boundary.
    """
    k = d.a.shape[1] - 1
    best = None
    rng = np.random.default_rng(seed)
    for start in [np.zeros(k), *(rng.normal(0, 1.0, size=(4, k)))]:
        r = minimize(_neg_log_likelihood, start, args=(d,), method="BFGS")
        r = minimize(_neg_log_likelihood, r.x, args=(d,), method="Nelder-Mead")
        # A non-finite objective is a FAILED start, not a candidate.
        #
        # The guard is not defensive tidiness; without it the multi-start is
        # silently defeated by its own comparison. `r.fun < best.fun` is False
        # whenever `best.fun` is NaN, because every comparison against NaN is
        # False. So a NaN from the FIRST start is never displaced by any later
        # start, however good, and `fit` returns a NaN model with no error, no
        # warning, and a `beta` of all-NaN that propagates into every metric
        # downstream. It was found on 2026-09-14 by a covariate experiment
        # whose only symptom was a `nan` in a printed mean.
        if not np.isfinite(r.fun):
            continue
        if best is None or r.fun < best.fun:
            best = r

    if best is None:
        # Every start failed. Raising beats returning NaN: a caller that gets
        # an exception stops, and a caller that gets NaN carries it into a
        # published number.
        raise RuntimeError(
            "choice.fit: all 5 starts returned a non-finite "
            f"log-likelihood on {d.n_decisions} decisions, "
            f"{d.a.shape[1]} attractions. The data, not the optimiser, is "
            "the thing to check -- a column of zeros or a choice set of one "
            "will do this.")

    beta = np.concatenate([[1.0], np.exp(best.x)])

    # POSITIVITY AT THE OPTIMUM, checked rather than assumed.
    #
    # `P(j|m) = beta'a_j / sum_k beta'a_k` is only a probability while
    # `beta'a > 0` for EVERY alternative, chosen or not. The module docstring
    # says the exp parameterisation "enforces it" -- and that is true only
    # while every attraction column is non-negative. It is not true the moment
    # a centred or log-relative column is added, because a positive
    # coefficient on a negative column SUBTRACTS attraction.
    #
    # The failure is silent and it flatters the fit. Measured 2026-09-14 on
    # log-relative arms: the optimiser drove coefficients 20x to 77x past the
    # feasibility ceiling, pushing 765-4,816 NON-CHOSEN alternatives below
    # zero. That shrinks the denominator, inflates P(chosen) from 0.078685 to
    # 0.079346, and raises the log-likelihood by up to 1.20 -- while
    # `negative_and_chosen` stays 0, so no term in the objective ever becomes
    # undefined and nothing complains. The tell was that in all five columns,
    # the direction with the LOWER feasibility ceiling was the one that
    # "found" a coefficient: success was predicted by how cheap it was to
    # violate positivity.
    #
    # The non-finite-start guard above does NOT catch this. An infeasible
    # optimum has a perfectly finite log-likelihood; that is the whole problem.
    utility = d.a @ beta
    n_bad = int((utility <= 0).sum())
    if n_bad:
        raise ValueError(
            f"choice.fit: the optimum puts beta'a <= 0 on {n_bad} of "
            f"{len(utility)} alternatives (min {utility.min():.6g}), so "
            "P(j|m) is not a probability there. This happens when an "
            "attraction column takes negative values -- a centred, "
            "log-relative or differenced column -- because a positive "
            "coefficient on a negative column subtracts attraction. The "
            "likelihood is still finite and still improves, which is why it "
            "must be checked here rather than left to the optimiser. Enter "
            "such a covariate through a separate unconstrained linear index, "
            "not inside ln(beta'a). See "
            "experiments/percapita-logrel/notes/NOTES_LOG_RELATIVE.md.")

    ll = -best.fun
    # A uniform-within-choice-set null: the honest "no information" model for
    # a choice problem, and the right comparator for McFadden's rho-squared.
    sizes = np.bincount(d.group)
    ll0 = -float(np.log(sizes).sum())
    return {
        "beta": dict(zip(d.names, beta.tolist(), strict=True)),
        "theta": best.x.tolist(),
        "n_parameters": k,
        "numeraire": NUMERAIRE,
        "log_likelihood": ll,
        "log_likelihood_uniform": ll0,
        "mcfadden_rho_squared": 1.0 - ll / ll0 if ll0 else float("nan"),
        "n_decisions": d.n_decisions,
        "converged": bool(best.success),
    }


def predict(theta: np.ndarray, d: ChoiceData) -> np.ndarray:
    """Choice probabilities for every alternative."""
    return _probabilities(np.asarray(theta, float), d)


def evaluate(theta: np.ndarray, d: ChoiceData) -> dict:
    """Brier PAIR and calibration against a uniform-within-set null.

    The raw pair, never the skill score: Gneiting & Raftery (2007) section 2.3
    p. 362 shows skill scores are generally improper even when the underlying
    score is proper. See `docs/research/NOTES_gneiting_raftery_2007.md`.
    """
    p = predict(theta, d)
    y = np.zeros(len(p))
    y[d.chosen] = 1.0
    sizes = np.bincount(d.group)
    uniform = 1.0 / sizes[d.group]

    def brier(pred):
        return float(np.mean((pred - y) ** 2))

    # Hit rate at K: how often is the true ZCTA in the model's top K for
    # its own metro? Reported alongside because a Brier score over tens of
    # thousands of near-zero alternatives is dominated by the zeros.
    def top_k(pred, k):
        hits = 0
        for g in range(d.n_decisions):
            rows = np.flatnonzero(d.group == g)
            order = rows[np.argsort(-pred[rows])]
            hits += int(d.chosen[g] in order[:k])
        return hits / d.n_decisions

    return {
        "n_decisions": d.n_decisions,
        "n_alternatives": int(len(p)),
        "brier": brier(p),
        "brier_uniform_null": brier(uniform),
        "mean_prob_of_chosen": float(p[d.chosen].mean()),
        "mean_prob_uniform": float(uniform[d.chosen].mean()),
        "top1": top_k(p, 1), "top1_uniform": top_k(uniform, 1),
        "top5": top_k(p, 5), "top5_uniform": top_k(uniform, 5),
        "top10": top_k(p, 10), "top10_uniform": top_k(uniform, 10),
    }
