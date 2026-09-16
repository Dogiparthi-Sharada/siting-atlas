"""What a conformal run puts in the metrics file, and what it must not.

Split out of ``conformal.py``: that module is the method, this one is the
record of what the method did. Keeping them apart matters more than it
sounds, because the two failure modes are completely different. A bug in the
method breaks the coverage guarantee. A bug here produces a guarantee that
is intact and a report of it that cannot be used — a number outside its own
range, or a token no JSON parser will accept — and that is easier to ship,
because every test that exercises the method still passes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def _json_number(value: float, digits: int) -> float | None:
    """Round for the report, but hand back null for a non-finite value.

    ``json.dumps(float("inf"))`` emits the bare token ``Infinity``. Python
    reads it back, and nothing else does: it is not JSON, and a strict parser
    — jq, most browsers' JSON.parse, every typed schema validator — rejects
    the whole document. An infinite q_hat is not a bug (it is the honest
    answer when the calibration sample is too small to support the requested
    level, see conformal_quantile) so the fix belongs at the serialisation
    boundary, not at the source.

    null, paired with the explicit ``q_hat_is_infinite`` flag beside it,
    keeps the file parseable without quietly turning "no finite threshold
    exists" into some large finite number that a downstream plot would
    happily draw.
    """
    return None if not math.isfinite(value) else round(float(value), digits)


@dataclass
class ConformalReport:
    """Measured behaviour of the conformal wrapper on a held-out sample."""

    alpha: float
    nominal_coverage: float
    empirical_coverage: float
    n_calibration: int
    n_test: int
    q_hat: float
    mean_set_size: float
    share_singleton: float
    share_full: float
    share_empty: float
    #: Independent units in the test sample. Rows, when the sample is not
    #: clustered; the number of ZCTAs when it is. Drives the tolerance band.
    n_effective: int = 0

    @property
    def tolerance(self) -> float:
        """Two-sigma Monte-Carlo band on the empirical coverage."""
        return coverage_tolerance(self.n_effective or self.n_test,
                                  self.alpha)

    @property
    def within_tolerance(self) -> bool:
        """Is the measured coverage consistent with the nominal level?

        Two-sided. Coverage far ABOVE nominal is not a success either — it
        means the sets are wider than they need to be, which is the price
        paid for the guarantee and worth noticing when it is being overpaid.
        """
        return abs(self.empirical_coverage - self.nominal_coverage) <= (
            self.tolerance + 1.0 / (self.n_calibration + 1))

    @property
    def finite_sample_upper_bound(self) -> float:
        """Coverage cannot exceed this by more than sampling noise.

        The guarantee is two-sided when the scores are continuous:
        1-alpha <= coverage <= 1-alpha + 1/(n_cal+1). Reporting the upper
        bound alongside the lower one is what distinguishes "the method
        works" from "the sets are so wide that coverage is trivially 100%".

        Capped at 1. The raw expression exceeds 1 whenever the calibration
        sample is smaller than 1/alpha — with three rows at alpha=0.10 it
        returns 1.15 — and a printed "upper bound on coverage: 1.0111" is
        worse than useless: coverage is a probability, so a reader who
        notices the impossible value loses confidence in the whole table,
        and one who does not notice reads the guarantee as looser than it
        is. 1.0 is both true and binding.
        """
        return min(1.0, self.nominal_coverage + 1.0 / (self.n_calibration
                                                       + 1))

    def to_dict(self) -> dict:
        return {"alpha": self.alpha,
                "nominal_coverage": round(self.nominal_coverage, 4),
                "empirical_coverage": round(self.empirical_coverage, 4),
                "upper_bound": round(self.finite_sample_upper_bound, 4),
                "tolerance_2sigma": _json_number(self.tolerance, 4),
                "within_tolerance": bool(self.within_tolerance),
                "n_calibration": self.n_calibration, "n_test": self.n_test,
                "n_effective": self.n_effective or self.n_test,
                "q_hat": _json_number(self.q_hat, 6),
                "q_hat_is_infinite": bool(not math.isfinite(self.q_hat)),
                "mean_set_size": round(self.mean_set_size, 4),
                "share_singleton": round(self.share_singleton, 4),
                "share_full": round(self.share_full, 4),
                "share_empty": round(self.share_empty, 4)}

    def summary(self) -> str:
        return (f"conformal alpha={self.alpha:.2f}: nominal "
                f"{self.nominal_coverage:.1%}, empirical "
                f"{self.empirical_coverage:.1%} +/- {self.tolerance:.1%} "
                f"on {self.n_test:,} rows (q_hat={self.q_hat:.4f}, mean set "
                f"size {self.mean_set_size:.3f})")


def coverage_tolerance(n_effective: int, alpha: float = 0.10,
                       n_sigma: float = 2.0) -> float:
    """How far empirical coverage can miss nominal by chance alone.

    The binomial standard error of a coverage estimate is
    sqrt(c(1-c)/n_effective). The word doing the work is EFFECTIVE: for a
    clustered test sample, ``n_effective`` is the number of UNITS, not the
    number of rows. Using rows would give a band of half a percentage point
    on a quantity whose real replication spread is three times that, and
    every ordinary run would then look like a failure of the method.

    Taking n_effective = number of units assumes rows within a unit are
    perfectly correlated. They are not quite, so the band is slightly
    conservative — which is the correct direction for a tolerance whose job
    is to stop people over-reading noise.
    """
    if n_effective <= 0:
        return float("inf")
    c = 1.0 - alpha
    return float(n_sigma * math.sqrt(c * (1 - c) / n_effective))
