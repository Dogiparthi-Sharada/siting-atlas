"""Analyses that ask a question the target variable cannot answer.

Everything in ``models/`` answers *"where did Amazon build?"* and is capped by
the 485 decisions that question has. This package holds the analyses that need
no target at all — today, exactly one: :mod:`.white_space`, which inverts the
map and asks where the demand Amazon has NOT reached is.

The modules here read the delivered panel and the facility frames and write
to ``outputs/metrics/``. They fit nothing, so they cannot overfit; the price
is that they cannot be scored by AUC either, and each one has to say in its
own artefact how it would be falsified.
"""

from __future__ import annotations

__all__: list[str] = []
