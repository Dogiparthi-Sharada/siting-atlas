"""The hand-labelled batches, deduplicated, and delivered without dates.

Three batches of 70 OSHA buildings went out as PREVIOUSLY UNCLASSIFIED sites
and 85 came back delivery stations. They were not unclassified: 289 of the
worklist's 362 rows carry an address and state ``NATIONAL_CLASSIFIED.csv``
already holds, and that is the file ``national_facilities.csv`` was built
from. Matched on parsed ADDRESS with the project's Fellegi-Sunter comparator
-- never on a city string, which is what the HAWTHORNE/HOLLYGLEN pair breaks
-- **76 of the 85 are already in a facility frame**, 52 national and 24
pilot. Nine are new, and each lands in a CBSA the national frame does not
hold, so they add metros rather than the density they were collected for.

The date decision is that there is no date. These rows carry OSHA's
``operating_by``, an UPPER bound with a measured lag to the true opening of 4
to 345 months (``FACILITY_PANEL_PROVENANCE`` Sec. 6.2, n=5, median 57).
``models/choice.build`` scores a facility on the latest CBP vintage strictly
earlier than ``open_year`` because a delivery station IS a warehousing
establishment; write a bound into that field and a vintage before the BOUND
can still be after the OPENING, re-entering the circularity the lag exists to
prevent through the field the lag reads. So ``open_year`` is left empty and
the bound is carried under its own name. Sec. 19 weighs the alternatives and
records what the emptiness costs.

Emptiness is the instruction, not a gap the caller must remember:
``choice.build`` already drops a facility with no usable ``open_year`` when an
industry covariate is requested, and never reads the field when one is not.

Nothing here is merged into ``data/external/facility_panel/``. The choice
model is fitted on ``load_national()``, so adding rows there would move a
published number, and that is the inspirator's call rather than this module's.
"""

from __future__ import annotations

import json

import pandas as pd

from ..common import paths
from ..common.linkage import (
    MATCH,
    REVIEW,
    LinkRecord,
    candidate_pairs,
    compare,
)
from ..common.logging_setup import get_logger
from .edits import apply_operating_by, load_operating_bounds
from .geo_keys import zcta_cbsa_titles
from .national import first_in_metro, load_national

_log = get_logger("warehouse.batch_candidates")

RESULTS = paths.DATA / "collection" / "results"
PANEL_DIR = paths.EXTERNAL / "facility_panel"
CANDIDATES = RESULTS / "BATCH_DS_CANDIDATES.csv"
ARTEFACT = paths.METRICS / "batch_candidates.json"


def _batches() -> tuple[str, ...]:
    """Every labelled batch on disk, discovered rather than listed.

    This was `BATCHES = ("1", "2", "3")`, written when three existed. Three
    more landed and the constant did not move, so the module silently read
    210 of 362 rows and emitted nine candidates where there are thirteen.
    Nothing failed; the answer was just quietly short, which is the worst
    way for a data pipeline to be wrong.

    Sorted numerically, not lexically, so batch 10 does not fall between 1
    and 2 the day somebody runs a tenth.
    """
    found = sorted(
        (p.stem.split("_")[2] for p in
         RESULTS.glob("UNLABELLED_BATCH_*_CLASSIFIED.csv")),
        key=lambda s: (len(s), s))
    if not found:
        _log.warning("no UNLABELLED_BATCH_*_CLASSIFIED.csv in %s",
                     paths.rel(RESULTS))
    return tuple(found)

DELIVERY_STATION = "DS"

#: ``national_facilities.csv``'s columns in its own order, so the candidate
#: file concatenates onto it the day a lower bound arrives, plus the bound
#: under the name that says what it is.
SCHEMA = ("facility_id", "operator", "facility_type", "city", "state", "zip",
          "site_address", "latitude", "longitude", "open_year",
          "open_quarter", "close_year", "close_quarter", "square_feet",
          "status", "source_url", "source_type", "confidence", "cbsa_title",
          "osha_operating_by")


def load_batches(directory=None) -> pd.DataFrame:
    """The three classified batches, stacked, with one label column.

    Batch 1 names the verbatim answer ``gemini_label`` and batches 2 and 3
    name it ``label``. Renaming here rather than at each call site is what
    stops an UNKNOWN in one batch being read as a missing answer in another.
    """
    directory = directory or RESULTS
    frames = []
    for batch in _batches():
        path = directory / f"UNLABELLED_BATCH_{batch}_CLASSIFIED.csv"
        frame = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
        frames.append(frame.rename(columns={"gemini_label": "label"}))
    return pd.concat(frames, ignore_index=True).fillna("")


def load_existing(panel_dir=None) -> pd.DataFrame:
    """Both facility frames, as addresses with a frame label.

    Read RAW, before ``E_operating_by`` runs. A row the edit excludes is
    still a building that exists, so re-admitting it from a batch would
    create a duplicate rather than recover a loss.
    """
    panel_dir = panel_dir or PANEL_DIR
    out = []
    for name, label in (("national_facilities.csv", "national"),
                        ("facilities.csv", "pilot")):
        frame = pd.read_csv(panel_dir / name, dtype=str,
                            encoding="utf-8-sig").fillna("")
        frame["frame"] = label
        out.append(frame[["facility_id", "frame", "site_address", "city",
                          "state", "zip"]])
    return pd.concat(out, ignore_index=True)


def _records(frame: pd.DataFrame, rid, *cols) -> list[LinkRecord]:
    """The frame as link records. ``rid`` is a column name, or ``None`` for
    the positional index — which is what the batch side needs to map back."""
    return [LinkRecord.build(str(i) if rid is None else r[rid],
                             *(r[c] for c in cols))
            for i, r in frame.iterrows()]


def split_on_links(batch: pd.DataFrame,
                   existing: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Split the batch into rows new to both frames and rows already in one.

    Refuses on a REVIEW-band link rather than deciding it. Admitting an
    unsure pair counts one building twice in the within-metro density this
    exercise exists to raise; dropping it deletes a real facility. Neither is
    settled by the comparator, so it goes to a human --
    ``facility_load._refuse_unresolved`` sets the precedent.
    """
    left = _records(batch, None, "site_address", "site_city", "site_state",
                    "site_zip")
    right = _records(existing, "facility_id", "site_address", "city", "state",
                     "zip")
    n = len(left)
    seen: dict[int, list[str]] = {}
    held: list[str] = []
    for a, b in candidate_pairs(left + right):
        if (a < n) == (b < n):
            continue
        i, j = (a, b - n) if a < n else (b, a - n)
        verdict = compare(left[i], right[j])
        if verdict.call == MATCH:
            seen.setdefault(i, []).append(right[j].rid)
        elif verdict.call == REVIEW:
            held.append(f"{batch.iloc[i]['site_address']} / "
                        f"{right[j].rid}: {verdict.why}")
    if held:
        raise ValueError(
            f"{len(held)} batch row(s) are held for clerical review against "
            "the existing frames and cannot be dispatched mechanically:\n    "
            + "\n    ".join(held) + "\nAdmitting one double-counts a "
            "building; dropping one deletes a facility. Resolve by "
            "inspection, not by moving common/linkage.py's thresholds.")

    by_id = existing.set_index("facility_id")["frame"].to_dict()
    duplicates = [{"site_address": batch.iloc[i]["site_address"],
                   "site_city": batch.iloc[i]["site_city"],
                   "site_state": batch.iloc[i]["site_state"],
                   "batch": batch.iloc[i]["batch"],
                   "item": batch.iloc[i]["item"],
                   "matches": sorted(ids),
                   "frames": sorted({by_id[k] for k in ids})}
                  for i, ids in sorted(seen.items())]
    fresh = batch.drop(index=[batch.index[i] for i in seen])
    return fresh.reset_index(drop=True), duplicates


def _cbsa_by_zcta() -> pd.Series | None:
    """The ZCTA->CBSA bridge, or ``None`` when the crosswalks are not built.

    ``None`` rather than an exception, for the reason
    ``edits.load_operating_bounds`` gives: these are build products a fresh
    clone will not have, and an unresolved metro is a different state from a
    ZCTA that is genuinely in none.
    """
    needed = {n: paths.INTERIM / f"{n}.parquet"
              for n in ("zcta_county", "cbsa_county", "cbp")}
    if not all(p.exists() for p in needed.values()):
        _log.warning("no ZCTA->CBSA crosswalk on disk; every candidate will "
                     "come back unplaced and the metro counts are NOT zero, "
                     "they are unmeasured")
        return None
    return zcta_cbsa_titles(*(pd.read_parquet(needed[n]) for n in
                              ("zcta_county", "cbsa_county", "cbp")))


def _to_schema(fresh: pd.DataFrame, cbsa: pd.Series | None) -> pd.DataFrame:
    """The candidate rows in the national frame's own column order."""
    zips = fresh["site_zip"].str.strip().str.zfill(5)
    out = pd.DataFrame({
        "facility_id": [f"CAND-B{r['batch']}-{int(r['item']):03d}"
                        for _, r in fresh.iterrows()],
        "operator": "Amazon",
        "facility_type": fresh["facility_type"],
        "city": fresh["site_city"], "state": fresh["site_state"],
        "zip": zips, "site_address": fresh["site_address"],
        "latitude": pd.NA, "longitude": pd.NA,
        # THE DECISION. Empty, not imputed, not the bound.
        "open_year": pd.NA, "open_quarter": pd.NA,
        "close_year": pd.NA, "close_quarter": pd.NA, "square_feet": pd.NA,
        "status": "open", "source_url": fresh["source_url"],
        "source_type": "web_evidence", "confidence": "high",
        "cbsa_title": zips.map(cbsa) if cbsa is not None else pd.NA,
        "osha_operating_by": fresh["operating_by"],
    })
    return out[list(SCHEMA)]


def select(directory=None, panel_dir=None) -> tuple[pd.DataFrame, dict]:
    """The delivery stations new to both frames, and what they would buy."""
    batches = load_batches(directory)
    stations = batches[batches["facility_type"] == DELIVERY_STATION]
    existing = load_existing(panel_dir)
    fresh, duplicates = split_on_links(stations, existing)

    cbsa = _cbsa_by_zcta()
    frame = _to_schema(fresh, cbsa)
    frame, failures = apply_operating_by(
        frame.assign(open_q_index=float("nan")), load_operating_bounds(),
        label=paths.rel(CANDIDATES))
    frame = frame.drop(columns=["open_q_index", "open_date_falsified"])
    frame["osha_operating_by"] = fresh["operating_by"].to_numpy()

    # The BASELINE is the frame the choice model actually sees -- after
    # E_operating_by, 100 rows, not the 104 in the file. Comparing against
    # the raw file would credit the candidates with a denominator no fit
    # uses and put the before-share at 62.5% instead of 65.0%.
    national = load_national((panel_dir or PANEL_DIR)
                             / "national_facilities.csv")
    nat_titles = set(national["cbsa_title"].dropna())
    titles = set(frame["cbsa_title"].dropna())
    before = first_in_metro(national)
    after = before + first_in_metro(frame)

    report = {
        "batch_rows": int(len(batches)),
        "unknown_answers": int((batches["label"] == "UNKNOWN").sum()),
        "delivery_stations": int(len(stations)),
        "already_in_a_frame": len(duplicates),
        "in_national": sum(1 for d in duplicates if "national" in d["frames"]),
        "in_pilot": sum(1 for d in duplicates if "pilot" in d["frames"]),
        "candidates": int(len(frame)),
        "cbsas": len(titles),
        "cbsas_new_to_national": len(titles - nat_titles),
        "unplaced_in_any_cbsa": int(frame["cbsa_title"].isna().sum()),
        "operating_by_failures": failures,
        "edit_note": (
            "E_operating_by compares a CLAIMED opening against the bound. "
            "Every candidate claims nothing, so the edit passes by "
            "construction and the empty failure list above corroborates "
            "no date."),
        "first_in_metro_share_before": round(before / len(national), 4),
        "first_in_metro_share_after": round(
            after / (len(national) + len(frame)), 4),
        "duplicates": duplicates,
    }
    return frame, report


def summarise(out_path=None, csv_path=None, **kwargs) -> dict:
    """Write the candidate CSV and the artefact. Returns what it wrote."""
    frame, report = select(**kwargs)
    csv_path = csv_path or CANDIDATES
    out_path = out_path or ARTEFACT
    for path in (csv_path, out_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(csv_path, index=False)
    report["candidate_file"] = paths.rel(csv_path)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=False)
        fh.write("\n")
    _log.info("%d batch row(s) -> %d delivery station(s); %d already in a "
              "frame (%d national, %d pilot); %d candidate(s) in %d CBSA(s), "
              "all undated. First-in-metro share %.1f%% -> %.1f%%",
              report["batch_rows"], report["delivery_stations"],
              report["already_in_a_frame"], report["in_national"],
              report["in_pilot"], report["candidates"], report["cbsas"],
              100 * report["first_in_metro_share_before"],
              100 * report["first_in_metro_share_after"])
    return report


def main() -> int:
    from ..common.context import init_run
    from ..common.logging_setup import configure

    paths.ensure_dirs()
    init_run()
    configure()
    r = summarise()
    print(f"\n  {r['batch_rows']} batch rows, {r['delivery_stations']} "
          f"delivery stations, {r['unknown_answers']} UNKNOWN\n"
          f"    {r['already_in_a_frame']} already in a frame "
          f"({r['in_national']} national, {r['in_pilot']} pilot)\n"
          f"    {r['candidates']} candidates, {r['cbsas']} CBSAs, "
          f"{r['cbsas_new_to_national']} new to the national frame\n"
          f"    first-in-metro share "
          f"{100 * r['first_in_metro_share_before']:.1f}% -> "
          f"{100 * r['first_in_metro_share_after']:.1f}%\n\n"
          f"  -> {r['candidate_file']}\n  -> {paths.rel(ARTEFACT)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
