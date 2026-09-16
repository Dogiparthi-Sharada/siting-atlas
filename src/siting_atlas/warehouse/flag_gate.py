"""L3 gate — a quality flag that is computed must reach the panel.

Why this exists
---------------
Three separate defects found by ``docs/data/DATA_QUALITY.md`` turned out to be
the same defect wearing different clothes. In each case something upstream
*noticed* a problem, wrote a boolean recording it, and the pipeline then
dropped the boolean on the way to ``panel.parquet``:

  * ``median_home_value_topcoded`` / ``median_household_income_topcoded``
    (``ingest/census_api.py``) — 83 and 86 ZCTAs whose value is a censoring
    code, present in ``data/interim/acs5_zcta_2023.parquet`` and absent from
    the panel's 44 columns.
  * ``wage_suppressed`` (``ingest/normalise_external.py``) — BLS withheld the
    estimate or top-coded it at >= $239,200; present in
    ``data/interim/bls_wages.parquet`` and absent from the panel.

Van den Broeck et al. (2005) separate *screening* from *editing* precisely so
that a flagged value can be carried into the analysis and reasoned about
there. A flag that dies between two layers is a screening step that was
performed and then discarded — the worst of both worlds, because the cost was
paid and the benefit was not. The panel is the only artefact any model reads,
so "reached the panel" is the operational meaning of "was not discarded".

What it checks
--------------
Every flag declared in ``common/sentinels.REGISTRY``, plus every column in an
L1 interim artefact whose name ends in one of :data:`FLAG_SUFFIXES`, must
appear as a column of the panel. There is deliberately no exemption list: a
flag that genuinely cannot be carried should force a decision and a comment,
not a quiet entry in a dictionary.

The registry is checked as well as the artefacts because the two fail
differently. A declared flag missing from the interim parquet means the
detector never ran; a flag in the parquet and not in the panel means the
warehouse dropped it. Both end as "the panel cannot see it", and both should
stop the build.

The check is name-based rather than type-based on purpose. The naming
convention is the contract — ``rent_observed``, ``income_imputed``,
``wage_suppressed`` and ``*_topcoded`` were all written by different people at
different times and all follow it — and a type check would miss a flag stored
as 0/1 while passing an unrelated boolean.
"""

from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq

from ..common import paths
from ..common.logging_setup import get_logger
from ..common.sentinels import all_flags

_log = get_logger("panel.flag_gate")

#: A column whose name ends in one of these is a data-quality flag: it records
#: something about how a value came to be, not a measurement of the world.
#: ``_observed`` is availability, ``_imputed`` is a filled value, ``_topcoded``
#: / ``_bottomcoded`` / ``_censored`` are bounds reported as points, and
#: ``_suppressed`` is a publisher withholding a cell.
FLAG_SUFFIXES = ("_imputed", "_topcoded", "_bottomcoded", "_censored",
                 "_observed", "_suppressed")


def is_flag(column: str) -> bool:
    """True when a column name follows the quality-flag convention."""
    return column.endswith(FLAG_SUFFIXES)


def computed_flags(interim: Path | None = None) -> dict[str, str]:
    """Every quality flag any L1 artefact computes, mapped to its artefact.

    Reads the parquet footer only — no column is materialised, so this stays
    cheap enough to run on every build.
    """
    interim = interim or paths.INTERIM
    found: dict[str, str] = {}
    for path in sorted(Path(interim).glob("*.parquet")):
        try:
            names = pq.read_schema(path).names
        except (OSError, ValueError) as exc:      # truncated or not parquet
            _log.warning("could not read the schema of %s (%s); its flags "
                         "cannot be checked", paths.rel(path), exc)
            continue
        for column in names:
            if is_flag(column):
                found.setdefault(column, path.stem)
    return found


def dropped_flags(panel_columns, computed: dict[str, str]) -> dict[str, str]:
    """The flags that were computed upstream and are not in the panel."""
    have = set(panel_columns)
    return {flag: src for flag, src in computed.items() if flag not in have}


def check(panel_columns, *, interim: Path | None = None,
          extra: dict[str, str] | None = None,
          declared: dict[str, str] | None = None) -> dict:
    """Gate report: which flags exist upstream, and which were lost.

    Two sources of truth, on purpose. The declared sentinel registry
    (``common/sentinels.py``) is authoritative for substitute codes and
    catches a flag that was declared and never even computed; the suffix scan
    over ``data/interim/`` catches the ones nobody thought to declare, such as
    ``wage_suppressed``. Either alone would have missed part of the defect.

    ``extra`` names flags computed inside the warehouse rather than in an
    interim parquet — ``warehouse/facility_load.py`` computes
    ``open_quarter_imputed`` from a CSV that never becomes an L1 artefact.
    ``declared`` overrides the registry and exists so the gate's own tests can
    exercise the mechanism without the project's real flags in the way.
    """
    registry = all_flags() if declared is None else declared
    computed = {flag: f"sentinel registry: {src}"
                for flag, src in registry.items()}
    computed.update(computed_flags(interim))
    computed.update(extra or {})
    missing = dropped_flags(panel_columns, computed)
    return {"computed": computed, "dropped": missing,
            "carried": sorted(set(computed) - set(missing))}


def assert_flags_carried(db, table: str = "panel", *,
                         interim: Path | None = None,
                         extra: dict[str, str] | None = None,
                         declared: dict[str, str] | None = None) -> dict:
    """Fail the build when a computed quality flag never reached the panel.

    Raises ``ValueError`` naming each lost flag and the artefact that computed
    it, because the useful half of the error message is *where to go and look*.
    """
    columns = db.df(f"DESCRIBE {table}")["column_name"].tolist()
    report = check(columns, interim=interim, extra=extra,
                   declared=declared)

    if report["dropped"]:
        lost = "\n".join(f"    {flag:36} computed in {src}"
                         for flag, src in sorted(report["dropped"].items()))
        raise ValueError(
            f"{len(report['dropped'])} quality flag(s) are computed upstream "
            f"and never reach `{table}`:\n{lost}\n"
            "A flag that is computed and dropped is a screening step paid "
            "for and thrown away. Carry it into the panel, or delete the "
            "code that computes it — never leave it stranded between layers.")

    _log.info("flag gate: %d computed quality flag(s), all carried into %s "
              "(%s)", len(report["computed"]), table,
              ", ".join(report["carried"]) or "none")
    return report
