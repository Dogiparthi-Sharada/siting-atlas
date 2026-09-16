"""Tests for what a ConformalReport puts in the metrics file.

Separate from ``test_conformal.py`` because the subject is different: that
file asks whether the coverage guarantee holds, this one asks whether the
number describing it can survive being written down and read back. Both
defects here are of the same kind — a value that is arithmetically defensible
and then impossible to use. An infinite q_hat is the correct answer and an
unparseable one; an upper bound of 1.0111 is the correct arithmetic on a
quantity that cannot exceed 1.
"""

from __future__ import annotations

import json

import numpy as np

from siting_atlas.models.conformal import SplitConformalBinary


def test_an_infinite_q_hat_still_serialises_to_valid_json():
    """``json.dumps(inf)`` writes the bare token ``Infinity``, which is not
    JSON.

    Python reads its own output back, so a round trip inside the test suite
    proves nothing. Everything else rejects the file: jq, ``JSON.parse``,
    every schema validator. ``hazard_report.json`` is the artefact the whole
    L4 layer exists to produce, and an infinite q_hat is not an error — it is
    the honest answer when the calibration sample cannot support the
    requested level — so the report has to survive it.

    The failure mode is delayed and total: the run succeeds, the file is
    written, and the next tool in the chain cannot open it.
    """
    report = SplitConformalBinary(0.10).calibrate(
        np.array([0.2, 0.4, 0.6]), np.array([0, 1, 0])
    ).evaluate(np.array([0.01, 0.5]), np.array([0, 1]))

    payload = json.dumps(report.to_dict())
    assert "Infinity" not in payload and "NaN" not in payload

    def reject(token):
        raise AssertionError(f"strict parsers reject the token {token!r}")

    restored = json.loads(payload, parse_constant=reject)
    assert restored["q_hat"] is None
    assert restored["q_hat_is_infinite"] is True, (
        "null alone would read as 'not measured'; the flag says which")


def test_the_coverage_upper_bound_is_a_probability():
    """1 - alpha + 1/(n_cal+1) exceeds 1 on a small calibration sample.

    At eight calibration rows and alpha=0.10 it prints 1.0111. A coverage
    bound above 1 is not a rounding artefact, it is a statement that the set
    contains the truth more than always — and it appears in the same table
    as the empirical coverage it is supposed to bound, so a reader comparing
    the two is being handed a slack bound and told it is tight.
    """
    bounds = {}
    for n_cal in (3, 8, 50, 5_000):
        p_cal = np.linspace(0.05, 0.95, n_cal)
        y_cal = (np.arange(n_cal) % 3 == 0).astype(int)
        report = SplitConformalBinary(0.10).calibrate(
            p_cal, y_cal).evaluate(np.array([0.2, 0.8]), np.array([0, 1]))
        bounds[n_cal] = report.finite_sample_upper_bound
        assert 0.9 <= bounds[n_cal] <= 1.0, f"n_cal={n_cal} gave " \
                                            f"{bounds[n_cal]}"
        assert report.to_dict()["upper_bound"] <= 1.0

    # Capping must not blunt the bound where it is genuinely informative:
    # at 5,000 calibration rows the correction is 0.0002 and the bound has
    # to stay just above nominal, not collapse to 1.
    assert bounds[5_000] < 0.9003
    assert bounds[8] == 1.0, "1/(8+1) alone would have said 1.0111"
