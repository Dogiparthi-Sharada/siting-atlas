"""True (MWPVL-stated) opening years for the national panel, and the
self-count measurement those dates make possible.

WHY THIS FILE EXISTS
--------------------
``national_facilities.csv`` dates every building by the quarter of its
earliest OSHA inspection. An inspection proves the building was already
operating, so the date is an UPPER BOUND and the true opening is earlier by
an unknown amount -- measured at a median 34 months in
``docs/research/NOTES_COVARIATE_LEAKAGE.md``. MWPVL states opening months
outright. Where the same building appears in both, the pair gives one OSHA
bound and one stated date for the same site, which is what the decisive
leakage test needs.

THE MATCH IS THE PROJECT'S EXISTING RULE, ON A WIDER INPUT
-----------------------------------------------------------
No new matching rule is defined here. ``warehouse/mwpvl_merge._cross_screen``
is called unchanged -- the Fellegi-Sunter comparator over parsed addresses
from ``common/linkage.py`` -- and only its MATCH verdicts are used. The
REVIEW band is clerical review and is not a date.

One thing IS different from ``mwpvl_merge``: every MWPVL table is screened,
not only the two delivery-station tables. ``mwpvl_merge`` restricts to
delivery stations because it is BUILDING A DELIVERY-STATION PANEL and a
Japanese mini-station has no business in it. Here nothing is added to any
panel; the question is only "does MWPVL state a date for the building at
this address", and MWPVL files some of these addresses under inbound cross
dock or fulfilment centre. Restricting to the two DS tables costs half the
sample (15 usable decisions instead of 29). Both are reported: see
``DELIVERY_STATION_TABLES`` in the caller, which runs the DS-only set as a
sensitivity.

The cost is stated rather than absorbed. 14 of the 29 dates used come from a
table for a DIFFERENT facility class at the same street address. That is
either a co-located site, an MWPVL table assignment this project cannot
audit, or an address match that is right about the building and wrong about
the business. None of the three is repaired here.

NOTHING IS CORRECTED
--------------------
Two of the 29 MWPVL dates are LATER than the OSHA bound for the same
building, which the project's own ``E_operating_by`` edit would call
impossible. They are kept and counted, because dropping the pairs that
disagree in the inconvenient direction is how a leakage test is rigged.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common import paths
from ..warehouse import mwpvl_geo
from ..warehouse.mwpvl_merge import (
    DELIVERY_STATION_TABLES,
    NATIONAL,
    _cross_screen,
    _link_records,
)
from ..warehouse.mwpvl_shape import to_panel_rows

MWPVL = paths.INTERIM / "mwpvl_facilities.csv"

__all__ = ["true_open_years", "provenance", "self_count_delta"]


def true_open_years() -> pd.DataFrame:
    """One row per national facility MWPVL also lists, with its stated year.

    Columns: ``facility_id`` (the NAT id), ``true_open_year``,
    ``mwpvl_id``, ``mwpvl_table``, ``mwpvl_vouched``. Where two MWPVL rows
    match one building the EARLIER stated year wins, because the quantity
    wanted is the first date the site was operating and an earlier date is
    the more conservative choice for a test of whether the covariate was
    measured before the building existed.
    """
    if not MWPVL.exists():
        raise SystemExit(
            f"\n  {paths.rel(MWPVL)} not found, so there are no stated\n"
            "  opening dates and the decisive test cannot be run. Run:\n"
            "      python -m siting_atlas.ingest.mwpvl_tables\n")
    raw = pd.read_csv(MWPVL, encoding="utf-8-sig",
                      dtype=str).reset_index(drop=True)
    national = pd.read_csv(NATIONAL, encoding="utf-8-sig", dtype=str)

    geo, _ = mwpvl_geo.resolve(raw["postcode"])
    shaped = to_panel_rows(raw, geo)
    cross = _cross_screen(_link_records(shaped, "zip"),
                          _link_records(national, "zip"), shaped)

    year = pd.to_numeric(raw["open_year"], errors="coerce")
    year.index = shaped["facility_id"]
    table = shaped.set_index("facility_id")["mwpvl_table"].to_dict()
    vouched = shaped.set_index("facility_id")["mwpvl_vouched"].to_dict()

    best: dict[str, dict] = {}
    for mwpvl_id, panel_ids in cross["match"].items():
        stated = year.get(mwpvl_id)
        if pd.isna(stated):
            continue
        for panel_id in panel_ids:
            prior = best.get(panel_id)
            if prior is not None and prior["true_open_year"] <= int(stated):
                continue
            best[panel_id] = {
                "facility_id": panel_id,
                "true_open_year": int(stated),
                "mwpvl_id": mwpvl_id,
                "mwpvl_table": table[mwpvl_id],
                "mwpvl_vouched": bool(vouched[mwpvl_id]),
            }
    return pd.DataFrame(sorted(best.values(), key=lambda r: r["facility_id"]))


def provenance(dates: pd.DataFrame, keep: list[str],
               facilities: pd.DataFrame) -> dict:
    """Where the stated dates used actually came from, and how far they move.

    ``keep`` is the decision set the test was run on, so this describes the
    dates that were USED and not the ones that were available.
    """
    used = dates[dates["facility_id"].isin(keep)]
    bound = pd.to_numeric(facilities.set_index(
        facilities["facility_id"].astype(str))["open_year"], errors="coerce")
    gap = (used["facility_id"].map(bound).to_numpy(float)
           - used["true_open_year"].to_numpy(float))
    ds = used["mwpvl_table"].isin(DELIVERY_STATION_TABLES)
    return {
        "by_mwpvl_table": used["mwpvl_table"].value_counts().to_dict(),
        "from_a_delivery_station_table": int(ds.sum()),
        "from_another_facility_class": int((~ds).sum()),
        "mwpvl_vouched": int(used["mwpvl_vouched"].sum()),
        "gap_years_median": float(np.median(gap)),
        "gap_years_mean": float(gap.mean()),
        "stated_date_not_earlier_than_the_bound": int((gap <= 0).sum()),
    }


def self_count_delta(facilities: pd.DataFrame, panel: pd.DataFrame,
                     cbp: pd.DataFrame, true_year: dict[str, int],
                     attractions: tuple[str, ...],
                     column: str) -> pd.DataFrame:
    """Does the chosen ZCTA gain about one establishment the others do not?

    A prediction test cannot separate self-counting from agglomeration, but
    this can, without fitting anything. For each facility take the two CBP
    vintages the two arms would use -- the one behind its OSHA bound and the
    one behind its stated opening -- and ask how much ``column`` rose in the
    ZCTA the facility was actually built in, against how much it rose in the
    average alternative of the same metro over the same two vintages.

    If the building is counting itself, the chosen ZCTA should gain about
    ONE more than its peers. If warehouses are simply clustering, both
    should drift together.

    Returns one row per facility; nothing is aggregated here.
    """
    wide = cbp.pivot_table(index="zcta", columns="cbp_year", values=column,
                           aggfunc="first")
    zctas = panel.drop_duplicates("zcta")[
        ["zcta", "cbsa_code", *attractions]].dropna(subset=["cbsa_code"])
    for col in attractions:
        zctas = zctas[zctas[col].notna() & (zctas[col] > 0)]
    home = zctas.set_index("zcta")["cbsa_code"].to_dict()
    by_cbsa = {c: g["zcta"].tolist() for c, g in zctas.groupby("cbsa_code")}
    vintages = sorted(cbp["cbp_year"].unique().tolist())

    def count(zcta: str, vintage: int) -> float:
        # Absent from CBP means zero establishments, the same real zero
        # `ingest/cbp_detail` records. Not a missing value.
        try:
            value = wide.loc[zcta, vintage]
        except KeyError:
            return 0.0
        return 0.0 if pd.isna(value) else float(value)

    def vintage_before(y: int) -> int | None:
        earlier = [v for v in vintages if v < y]
        return max(earlier) if earlier else None

    rows = []
    for _, fac in facilities.iterrows():
        fid = str(fac.get("facility_id"))
        zcta = str(fac.get("zcta") or "").strip()
        cbsa = home.get(zcta)
        stated = true_year.get(fid)
        try:
            bound = int(float(fac.get("open_year")))
        except (TypeError, ValueError):
            continue
        if cbsa is None or stated is None:
            continue
        v_osha, v_true = vintage_before(bound), vintage_before(stated)
        if v_osha is None or v_true is None:
            continue
        peers = by_cbsa[cbsa]
        at_true = np.array([count(p, v_true) for p in peers])
        at_osha = np.array([count(p, v_osha) for p in peers])
        rows.append({
            "facility_id": fid, "zcta": zcta,
            "v_true": v_true, "v_osha": v_osha,
            "count_at_true_vintage": count(zcta, v_true),
            "count_at_osha_vintage": count(zcta, v_osha),
            "chosen_delta": count(zcta, v_osha) - count(zcta, v_true),
            "peer_mean_delta": float((at_osha - at_true).mean()),
            # The two column totals `choice.build` divides by. Carried so
            # the fitted coefficient can be put back into raw units, which
            # the two arms do not share: each scales the column by its own
            # mean, and the two arms read different vintages of it.
            "alt_total_true": float(at_true.sum()),
            "alt_total_osha": float(at_osha.sum()),
            "n_alternatives": len(peers),
        })
    frame = pd.DataFrame(rows)
    if len(frame):
        frame["excess"] = frame["chosen_delta"] - frame["peer_mean_delta"]
    return frame
