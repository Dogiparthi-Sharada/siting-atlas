"""L4 models — the discrete-time hazard and its uncertainty wrapper.

Read in this order:

    risk_set.py     dense panel -> risk set. Read this one first; the trap
                    it prevents is silent and biases every coefficient.
    base.py         the Model contract, so specifications are swappable
    timebasis.py    the flexible baseline hazard in quarter-since-start
    hazard.py       DiscreteTimeHazard, cloglog link
    conformal.py    split conformal, the one distribution-free guarantee
    metrics.py      AUC, Brier, calibration curve and ECE
    splits.py       train/calibration/test, split by UNIT not by row
    fixtures.py     SYNTHETIC panel with a known DGP, for validating the
                    code before the target variable exists
    panel_source.py real panel if usable, labelled fixture if not; also
                    where the national panel is cut down to the metros a
                    fit is allowed to see
    diagnostics.py  what the real panel will NOT support, measured
    console.py      the terminal report, in reading order
    runner.py       the CLI

The facility panel HAS now arrived: 49 Amazon delivery stations, of which 44
open inside the window. ``fixtures.py`` and the ``SYNTHETIC_`` labelling stay
because they are what keeps an unpopulated target from being mistaken for a
result, but the default run is now real. Read ``diagnostics.py`` before
quoting any number from it — the target is small and its dates are OSHA
inspection upper bounds, and both facts change what the metrics mean.
"""
