"""Measure the study's scope, and write it where the documents can read it.

Why this module exists
----------------------
The proposal claimed "approximately 5,200 ZCTAs" in the ten pilot metros. The
measured figure, against the official OMB delineation, is 2,413. Nobody lied:
the number was estimated early, typed into nine places across the proposal,
the deck and four figures, and never checked against data again.

That is the failure mode this project is supposed to be about. So the scope
figures are computed once, from the same artefacts the model uses, written to
``outputs/metrics/scope.json``, and read by every document that quotes them. A
number in the proposal is now derived, not typed, and a change in the pilot
definition propagates instead of drifting.

    python -m siting_atlas.report.scope
"""

from __future__ import annotations

import pandas as pd

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.metros import REGISTRY
from ..common.trace import artefact, metric, step, traced_layer

_log = get_logger("scope")

# Assumptions, stated here rather than buried in a figure caption. Each is a
# declared input to a headline number, so each is auditable.
#
# Capital per activation: the range quoted in the proposal for standing up
# same-day service in one ZIP-code area, inclusive of the sortation capacity
# it implies. A range, not a point, because the estimate is a range.
CAPITAL_PER_ACTIVATION = (3_000_000, 5_000_000)

# Uncertainty draws: bootstrap replicates x conformal calibration splits x
# scenario paths. Reported because compute spent on inference is the honest
# answer to "your panel is small".
MC_DRAWS_PER_ZCTA = 10_000_000

# ZCTAs nationally, for the "if scaled" comparison. Counted from the
# gazetteer rather than typed: a round 33,000 sat here while the loaded
# universe was 33,791, which is the same defect this module was written to
# stop — and it fed a $99B-165B headline.
NATIONAL_ZCTAS_FALLBACK = 33_791


def measure() -> dict:
    """Compute every scope figure the documents quote."""
    delineation = pd.read_parquet(paths.INTERIM / "cbsa_county.parquet")
    xwalk = pd.read_parquet(paths.INTERIM / "zcta_county.parquet")

    gaz = paths.INTERIM / "gazetteer.parquet"
    national = (int(pd.read_parquet(gaz, columns=["zcta"])["zcta"].nunique())
                if gaz.exists() else NATIONAL_ZCTAS_FALLBACK)

    check = REGISTRY.validate(delineation)
    if not check["ok"]:
        # Not fatal, but it means the figures below describe a smaller pilot
        # than the one declared, so it must be impossible to miss.
        _log.error("scope measured against an incomplete pilot: %s missing",
                   ", ".join(check["missing"]))

    counties = REGISTRY.counties(delineation)
    tagged = counties.merge(xwalk, on="county_geoid", how="inner")

    by_metro = (tagged.groupby("metro_label")["zcta"].nunique()
                      .sort_values(ascending=False))
    n_zcta = int(tagged["zcta"].nunique())
    n_county = int(counties["county_geoid"].nunique())

    lo, hi = CAPITAL_PER_ACTIVATION
    scope = {
        "pilot": {
            "metros": len(REGISTRY),
            "metros_fit": sum(1 for m in REGISTRY if not m.heldout),
            "metros_heldout": sum(1 for m in REGISTRY if m.heldout),
            "counties": n_county,
            "zctas": n_zcta,
            "zctas_by_metro": {k: int(v) for k, v in by_metro.items()},
            "definition": "OMB 2023 CBSA delineation",
        },
        "capital": {
            "per_activation_usd": list(CAPITAL_PER_ACTIVATION),
            "low_usd": n_zcta * lo,
            "high_usd": n_zcta * hi,
            "label": f"${n_zcta * lo / 1e9:.1f}B-${n_zcta * hi / 1e9:.1f}B",
            "national_label": (f"${national * lo / 1e9:.0f}B-"
                               f"${national * hi / 1e9:.0f}B"),
        },
        "compute": {
            "draws_per_zcta": MC_DRAWS_PER_ZCTA,
            "draws_total": n_zcta * MC_DRAWS_PER_ZCTA,
            "label": f"{n_zcta * MC_DRAWS_PER_ZCTA / 1e9:.0f} billion",
            "search_space_label": f"2^{n_zcta:,}",
        },
        "national_zctas": national,
    }

    if paths.PANEL.exists():
        panel = pd.read_parquet(paths.PANEL, columns=["zcta"])
        scope["panel"] = {
            "rows": len(panel),
            "rows_label": f"{len(panel):,}",
            "megabytes": round(paths.PANEL.stat().st_size / 1e6, 1),
        }
    return scope


def main() -> int:
    """CLI entry point for L5. Measures scope and writes scope.json.

    Everything printed here is also in the JSON, which is what the proposal,
    the deck and the figures read — see tools/scope.py.
    """
    paths.ensure_dirs()
    init_run()
    configure()

    with traced_layer("L5", "measure study scope"), step("scope:measure"):
        scope = measure()
        out = paths.METRICS / "scope.json"
        write_json(out, scope)
        artefact(out, zctas=scope["pilot"]["zctas"])
        metric("pilot_zctas", scope["pilot"]["zctas"])
        metric("pilot_counties", scope["pilot"]["counties"])
        metric("capital_range", scope["capital"]["label"])

    p, c = scope["pilot"], scope["capital"]
    print(f"\n  {p['metros']} pilot metros "
          f"({p['metros_fit']} fit / {p['metros_heldout']} held out)")
    print(f"  {p['counties']:,} counties, {p['zctas']:,} ZCTAs "
          f"[{p['definition']}]")
    for label, n in p["zctas_by_metro"].items():
        print(f"      {label:26} {n:>5,}")
    print(f"  capital at risk : {c['label']}  "
          f"(${c['per_activation_usd'][0]/1e6:.0f}-"
          f"{c['per_activation_usd'][1]/1e6:.0f}M per activation)")
    print(f"  search space    : {scope['compute']['search_space_label']}")
    print(f"  -> {paths.rel(paths.METRICS / 'scope.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
