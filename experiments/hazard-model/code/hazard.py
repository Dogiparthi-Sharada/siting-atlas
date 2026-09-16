"""Discrete-time hazard with a complementary log-log link.

The quantity being modelled
---------------------------
Not "is this ZCTA served" but "given that it was NOT served at the start of
this quarter, does it become served during it". That conditional is the
hazard, and modelling it is what lets a ZCTA enabled in 2019 and one enabled
in 2024 contribute the evidence each actually carries instead of both
collapsing into a single 0/1 label with the timing thrown away.

Why cloglog and not logit
-------------------------
Enablement is a decision an operator takes in continuous time; we only see
it bucketed into quarters. The complementary log-log link is the discrete
observation of exactly that process. If an underlying continuous hazard is
proportional across units, then the probability of observing the event in a
given quarter is

    P(event in quarter t) = 1 - exp(-exp(alpha_t + x'beta))

which IS the cloglog link. The payoff is interpretive: beta is a log hazard
RATIO, the same quantity a Cox model reports, and it does not depend on how
finely time was bucketed. Re-cut the panel into months and the cloglog betas
are unchanged in expectation; the logit betas are not, because a log-odds
per quarter is not a log-odds per month.

The practical difference is modest when hazards are small — at a 2% quarterly
hazard, cloglog and logit coefficients agree to about 1% — and it matters
exactly where the interesting ZCTAs are, in the upper tail where the hazard
is no longer small. The asymmetry is also the right shape: cloglog approaches
1 faster than it approaches 0, which is the behaviour of a process that
cannot un-happen.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm

from ..common.logging_setup import get_logger
from .base import Model
from .coeftable import (
    Scaler,
    coefficient_table,
    entry_row_means,
    raw_scale_map,
)
from .risk_set import EVENT_COL, ID_COL, TIME_COL, validate_risk_set
from .timebasis import baseline_design

_log = get_logger("models.hazard")


@dataclass(frozen=True)
class HazardSpec:
    """One specification. Swap it, refit, compare — nothing else changes."""

    covariates: tuple[str, ...]
    baseline: str = "spline"          # 'spline' | 'dummies' | 'linear'
    n_knots: int = 4
    standardise: bool = True
    cluster_by_unit: bool = True
    #: Column defining the clusters for the robust covariance. The ZCTA
    #: default is right when a unit's own quarters are the only dependence.
    #: It is wrong for a facility panel, where one delivery station flips
    #: every ZCTA within fifteen miles in the same quarter: those are one
    #: draw, not eighty. ``cbsa_code`` absorbs that; the runner reports both.
    cluster_col: str = ID_COL
    max_iter: int = 100

    def summary(self) -> dict:
        return {"covariates": list(self.covariates),
                "baseline": self.baseline, "n_knots": self.n_knots,
                "standardise": self.standardise,
                "cluster_by_unit": self.cluster_by_unit,
                "cluster_col": self.cluster_col}


class DiscreteTimeHazard(Model):
    """Cloglog hazard on a prepared risk set.

    ``fit`` takes the output of :func:`risk_set.build_risk_set`, never a raw
    panel. That is a deliberate refusal to be helpful: silently building the
    risk set inside fit would let a caller pass a dense panel, get numbers
    back, and never learn that thirty-one rows per enabled ZCTA were
    fabricated non-events. The invariants are re-checked here anyway.
    """

    name = "cloglog-hazard"

    def __init__(self, spec: HazardSpec):
        super().__init__()
        self.spec = spec
        self.result = None            # statsmodels GLMResults
        self._scaler = Scaler()
        #: Clusters behind the robust covariance; its asymptotics need many.
        self.n_clusters = 0
        self._knots: np.ndarray | None = None
        self._names: list[str] = []
        #: Covariate values the baseline curve is reported AT. Unit-level,
        #: not row-level; coeftable.entry_row_means says why that is 13%.
        self._reference: np.ndarray = np.zeros(0)

    # -- design ----------------------------------------------------------
    def design(self, frame: pd.DataFrame, *, training: bool
               ) -> tuple[np.ndarray, list[str]]:
        """Assemble [intercept | time baseline | covariates].

        ``training`` controls whether the knots and the standardising
        moments are learned from this frame or reused. Every leakage bug in
        a model like this one hides in that distinction, so it is a required
        keyword argument rather than something inferred from state.
        """
        missing = [c for c in self.spec.covariates
                   if c not in frame.columns]
        if missing:
            raise KeyError(f"risk set is missing covariate(s) {missing}")
        if TIME_COL not in frame.columns:
            raise KeyError(
                f"{TIME_COL!r} missing — pass a frame from build_risk_set()")

        time_block, time_names, knots = baseline_design(
            frame[TIME_COL].to_numpy(), spec=self.spec.baseline,
            n_knots=self.spec.n_knots,
            knots=None if training else self._knots)
        if training:
            self._knots = knots

        x = frame.loc[:, list(self.spec.covariates)].to_numpy(dtype=float)
        if np.isnan(x).any():
            # An imputation decision belongs upstream where the reason for
            # the gap is known, not silently inside a model fit.
            n_bad = int(np.isnan(x).any(axis=1).sum())
            raise ValueError(
                f"{n_bad} row(s) carry a missing covariate; impute or drop "
                f"them explicitly before fitting so the choice is recorded")
        if training:
            # The moments are learned whether or not they are applied, so
            # that baseline_hazard() can always report the curve at the
            # covariate means rather than at an arbitrary zero.
            self._scaler.learn(x)
            # A covariate that does not vary is collinear with the intercept
            # and makes the design matrix singular. Left to statsmodels this
            # surfaces as "Singular matrix", which sends the reader hunting
            # through the time baseline; naming the column takes a minute
            # off the diagnosis. It happens easily in practice — a variable
            # can be constant within one metro slice and not overall.
            flat = [name for name, sd
                    in zip(self.spec.covariates, x.std(axis=0), strict=True)
                    if sd == 0]
            if flat:
                raise ValueError(
                    f"covariate(s) {flat} are constant in this sample, so "
                    f"they are collinear with the intercept and the design "
                    f"matrix is singular; drop them from the specification")
        if self.spec.standardise:
            x = self._scaler.apply(x)

        matrix = np.column_stack([np.ones(len(frame)), time_block, x])
        names = ["intercept", *time_names, *self.spec.covariates]
        return matrix, names

    # -- fit ---------------------------------------------------------------
    def fit(self, frame: pd.DataFrame) -> DiscreteTimeHazard:
        validate_risk_set(frame)
        x, names = self.design(frame, training=True)
        y = frame[EVENT_COL].to_numpy(dtype=float)
        # Learned here rather than inside design() because it needs the unit
        # column, which the design matrix deliberately does not carry.
        self._reference = entry_row_means(frame, self.spec.covariates,
                                          ID_COL, TIME_COL)

        n_events = int(y.sum())
        if n_events < 10 * x.shape[1]:
            # Ten events per parameter is the conventional floor for a
            # binary-outcome regression. Below it the coefficients are
            # driven by a handful of rows and the standard errors understate
            # how little is actually known.
            _log.warning(
                "%d events for %d parameters — below the ten-events-per-"
                "parameter rule of thumb; treat coefficients as indicative",
                n_events, x.shape[1])

        family = sm.families.Binomial(link=sm.families.links.CLogLog())
        model = sm.GLM(y, x, family=family)

        kwargs: dict = {"maxiter": self.spec.max_iter}
        cluster = self.spec.cluster_col
        if self.spec.cluster_by_unit and cluster in frame.columns:
            # A ZCTA appears in up to 32 rows and those rows are the same
            # place in consecutive quarters, not 32 independent draws.
            # Treating them as independent makes the standard errors far too
            # small; the point estimates are untouched, so the recovery
            # tests are unaffected either way.
            groups = frame[cluster].to_numpy()
            self.n_clusters = int(pd.unique(groups).size)
            if self.n_clusters < 30:
                # Asymptotic in the NUMBER OF CLUSTERS, not of rows: under
                # ~30 the sandwich is still biased down, so these SEs come
                # out less wrong than the naive ones rather than right.
                _log.warning("clustering on %r gives only %d clusters; the "
                             "robust covariance understates uncertainty "
                             "below about 30", cluster, self.n_clusters)
            kwargs["cov_type"] = "cluster"
            kwargs["cov_kwds"] = {"groups": groups}

        try:
            self.result = model.fit(**kwargs)
        except Exception as exc:   # noqa: BLE001 - re-raised with context
            raise RuntimeError(
                f"cloglog GLM failed to converge ({type(exc).__name__}: "
                f"{exc}). The usual cause is separation in the time "
                f"baseline: a quarter with zero events gives its dummy an "
                f"unbounded coefficient. Try baseline='spline'") from exc

        self._names = names
        self._fitted = True
        _log.info("fitted %s: %d rows, %d events, %d parameters, "
                  "log-likelihood %.2f", self.name, len(y), n_events,
                  x.shape[1], self.result.llf)
        return self

    # -- predict -----------------------------------------------------------
    def predict(self, frame: pd.DataFrame) -> pd.Series:
        self._require_fitted()
        x, _ = self.design(frame, training=False)
        eta = x @ np.asarray(self.result.params)
        # 1 - exp(-exp(eta)), written via expm1 so that a small hazard keeps
        # its precision instead of being computed as the difference of two
        # numbers very close to 1.
        hazard = -np.expm1(-np.exp(np.clip(eta, -50, 50)))
        return pd.Series(hazard, index=frame.index, name="hazard")

    # -- inspection --------------------------------------------------------
    def coefficients(self, *, original_scale: bool = True) -> pd.DataFrame:
        """Coefficient table, undoing standardisation by default.

        A coefficient on a standardised covariate answers "per standard
        deviation"; a reader of the report wants "per unit of the thing
        itself". Since the transform is linear the translation is exact and
        the WHOLE covariance matrix goes through it, not just the diagonal
        — the raw intercept is a linear combination of every fitted
        coefficient and inherits their covariances. See coeftable.py; the
        version of this that rescaled the standard errors elementwise
        reported an intercept SE 1.4x too narrow.
        """
        self._require_fitted()
        k = len(self.spec.covariates)
        transform = None
        if original_scale and self.spec.standardise and k:
            transform = raw_scale_map(len(self._names), k,
                                      self._scaler.sd, self._scaler.mean)
        return coefficient_table(self._names, self.result.params,
                                 self.result.cov_params(),
                                 transform=transform)

    def summary(self) -> dict:
        """Serialisable fit summary for the metrics file."""
        self._require_fitted()
        coef = self.coefficients()
        return {
            "specification": self.spec.summary(),
            "log_likelihood": float(self.result.llf),
            "aic": float(self.result.aic),
            "n_parameters": int(len(self._names)),
            "n_clusters": self.n_clusters,
            "converged": bool(self.result.converged),
            "coefficients": [
                {"term": r.term, "coefficient": round(r.coefficient, 6),
                 "std_error": round(r.std_error, 6),
                 "p_value": round(r.p_value, 6),
                 "hazard_ratio": round(r.hazard_ratio, 5)}
                for r in coef.itertuples(index=False)],
        }

    def baseline_hazard(self, t_values: np.ndarray) -> pd.DataFrame:
        """Fitted hazard for the average UNIT, quarter by quarter.

        This is the curve that justifies the flexible baseline: plot it and
        the build-out push and the pause are visible, and so is the fact
        that a straight line could not have represented either.

        "Average unit" and not "average ROW". The risk set gives a unit that
        survives the whole window thirty-two rows and one that enables early
        just two, so a row mean is a description of the survivors and sits
        on the wrong side of every covariate that predicts the event. That
        published this curve 13% low at every quarter. ``_reference`` is
        learned at fit time with one row per unit; see
        coeftable.entry_row_means.
        """
        self._require_fitted()
        frame = pd.DataFrame({TIME_COL: np.asarray(t_values)})
        for i, name in enumerate(self.spec.covariates):
            frame[name] = float(self._reference[i])
        return pd.DataFrame({"t": frame[TIME_COL],
                             "hazard": self.predict(frame).to_numpy()})
