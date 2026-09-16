"""The declared edit set, and the one edit that reaches outside the record.

What an edit is, and why it is not a reliability weight
-------------------------------------------------------
Fellegi & Holt build everything on a set of EDITS: logical constraints a record
must satisfy, declared once, checked mechanically, with the fields to change
derived from the constraints rather than specified alongside them (their
Criterion 2). ``facility_dedup`` already implements one of those, and then
implements something else as well:

    E_date_contradiction   two records the matcher calls one building must
                           carry one opening date        -- an EDIT
    Sec. 7 reliability     where the edit fails, prefer the date from the more
                           reliable provenance           -- a PREFERENCE

The difference decides what happens on a tie. A preference expresses a ranking
over values that are all admissible, so when both records carry
``source_type=permit`` nothing separates them and Sec. 1 option 2 says stop:
"one should, whenever possible, avoid 'manufacturing' data instead of
collecting it." An edit expresses a CONTRADICTION, and a contradiction does not
tie -- the record that fails it is out regardless of how reliable its source
claims to be.

That is why the three national contradictions were stuck. All six rows are
``permit``, so the weights tie three times, ``open_q_index`` is left ``NaN``
three times, and the load refuses. What breaks the deadlock is not a better
ranking. It is a second edit.

E_operating_by
--------------
    quarter_start(open_q_index)  <=  osha_operating_by

An OSHA inspection is conducted at a site that EXISTS AND IS OPERATING, so its
date is an upper bound on the opening -- this is the reading
``ingest/osha.py`` has always taken and the reason the column is named
``operating_by`` rather than ``open_date``. A record claiming the building
opened strictly after the date it was already operating is not less reliable
than its twin. It is impossible.

Quarter STARTS, not ends, on purpose. A claimed 2017Q4 opening against an
inspection on 2017-12-21 is consistent -- the building could have opened on
1 October -- and comparing quarter ends would falsify the true record along
with the false one.

Three things this edit is NOT
-----------------------------
1. **It is not independent corroboration for the national panel.** Every one
   of the 104 rows in ``national_facilities.csv`` matches an OSHA building,
   and 100 of them carry exactly the quarter of that building's earliest
   inspection. The file was built by classifying the OSHA extract
   (``FACILITY_PANEL_PROVENANCE`` Sec. 16.3), so ``source_type=permit`` is the
   mislabelling that section already admits for the pilot file. The edit is
   therefore an INTERNAL consistency check that finds four rows whose date
   departs from the source they were derived from -- and all four depart in
   the direction the source forbids, which is what makes them errors rather
   than research.
2. **It does not turn a bound into an opening.** The surviving dates are still
   OSHA upper bounds with a measured lag to the true opening of 4 to 345
   months (``FACILITY_PANEL_PROVENANCE`` Sec. 6.2). A larger frame of upper
   bounds is a larger frame of upper bounds.
3. **It does not correct anything.** The failing record is flagged and, where
   the caller asks for it, excluded. No value is overwritten, so the
   uncorrected data is recoverable by ignoring two columns.

Disposition
-----------
``EXCLUDE`` drops the failing record; ``REPORT`` flags it and leaves it in
place. The pilot panel runs in ``REPORT`` because enforcing there would remove
Austin's only building and move published numbers -- see
``facility_load.load_facilities``.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..common import paths
from ..common.linkage import MATCH, LinkRecord, candidate_pairs, compare
from ..common.logging_setup import get_logger

_log = get_logger("warehouse.edits")

#: Dispositions for a record that fails an edit. Van den Broeck permits three
#: editing choices -- correct, delete, leave unchanged -- and CORRECT is
#: deliberately absent here: an edit that rewrote the field it localised would
#: be the imputation rule specified independently of the edits that Fellegi &
#: Holt's Criterion 2 exists to abolish.
EXCLUDE = "exclude"
REPORT = "report"

#: Columns the edit adds. Both are annotations; neither is a value.
EDIT_COLUMNS = ("osha_operating_by", "open_date_falsified")


@dataclass(frozen=True)
class Edit:
    """One declared constraint.

    ``fields`` is the minimal set the failure localises to (Fellegi & Holt
    Corollary 2). ``source`` names the artefact the check needs, empty when
    the edit is internal to one record set.
    """

    name: str
    fields: tuple[str, ...]
    statement: str
    rationale: str
    source: str = ""


#: Every edit the facility panel is checked against. Adding one is adding a
#: row here and a function below -- not an ``if`` somewhere in a loader.
EDITS = (
    Edit(
        name="E_date_contradiction",
        fields=("open_q_index",),
        statement=("two records linked at or above linkage.STREET_MATCH must "
                   "carry the same open_q_index"),
        rationale=("One building has one opening date. Where the records "
                   "disagree the minimal cover is the single field "
                   "open_q_index (Fellegi & Holt Corollary 2); which VALUE "
                   "to keep is not settled by the edit and falls to the "
                   "Sec. 7 reliability weights in facility_dedup, or to "
                   "collection when those tie."),
    ),
    Edit(
        name="E_operating_by",
        fields=("open_q_index",),
        statement=("quarter_start(open_q_index) <= osha_operating_by, for a "
                   "facility the address matcher links to an OSHA building"),
        rationale=("An OSHA inspection is conducted at an operating "
                   "establishment, so its date is an upper bound on the "
                   "opening. A claimed opening strictly after it is "
                   "falsified by the record, not merely outranked by it. "
                   "This is the edit that resolves contradictions the Sec. 7 "
                   "weights tie on."),
        source="data/interim/osha_amazon.csv",
    ),
)


def edit_by_name(name: str) -> Edit:
    for edit in EDITS:
        if edit.name == name:
            return edit
    raise KeyError(f"no declared edit named {name!r}; have "
                   f"{[e.name for e in EDITS]}")


def load_operating_bounds(path=None) -> pd.DataFrame | None:
    """The OSHA 'operating by' bounds, or ``None`` when the extract is absent.

    ``None`` rather than an exception. The extract is a build product of a
    1.4 GB download that a fresh clone will not have, and an edit that cannot
    be evaluated is a different state from an edit that passes -- callers log
    the difference rather than silently reading a pass into a skip.
    """
    path = path or (paths.INTERIM / "osha_amazon.csv")
    if not path.exists():
        return None
    frame = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    missing = {"site_address", "operating_by"} - set(frame.columns)
    if missing:
        raise ValueError(f"{paths.rel(path)} is missing {sorted(missing)}; "
                         "rerun python -m siting_atlas.ingest.osha")
    return frame


def _quarter_start(q_index: float) -> pd.Timestamp:
    """The first day of the quarter an ``open_q_index`` names."""
    year, quarter = divmod(int(q_index), 4)
    return pd.Timestamp(year=year, month=3 * quarter + 1, day=1)


def _tightest_bounds(frame: pd.DataFrame,
                     osha: pd.DataFrame) -> dict[int, tuple[str, str]]:
    """Facility row index -> (earliest operating_by, OSHA activity number).

    Matching is the project's Fellegi-Sunter comparator over parsed addresses,
    not a join on city: the two sources spell the same street differently
    ("SAINT HELENS"/"ST HELENS", "GRANT LINE"/"GRANTLINE") and file the same
    building under different city names (HAWTHORNE/HOLLYGLEN, TEMPLE
    TERRACE/TAMPA). ``candidate_pairs`` supplies the same blocking the
    within-file matcher uses, so the two are not two different notions of
    "same building".
    """
    left = [LinkRecord.build(str(r.get("facility_id", i)),
                             str(r.get("site_address") or ""),
                             str(r.get("city") or ""),
                             str(r.get("state") or ""),
                             str(r.get("zcta") or r.get("zip") or ""))
            for i, r in enumerate(frame.to_dict("records"))]
    right = [LinkRecord.build(str(r.get("activity_nr", j)),
                              str(r.get("site_address") or ""),
                              str(r.get("site_city") or ""),
                              str(r.get("site_state") or ""),
                              str(r.get("site_zip") or ""))
             for j, r in enumerate(osha.to_dict("records"))]

    n = len(left)
    dates = osha["operating_by"].astype(str).tolist()
    best: dict[int, tuple[str, str]] = {}
    for a, b in candidate_pairs(left + right):
        # Only cross-source pairs; within-file links are E_date_contradiction's
        # business and are adjudicated elsewhere.
        if (a < n) == (b < n):
            continue
        i, j = (a, b - n) if a < n else (b, a - n)
        if compare(left[i], right[j]).call != MATCH:
            continue
        date = dates[j][:10]
        if i not in best or date < best[i][0]:
            best[i] = (date, right[j].rid)
    return best


def check_operating_by(frame: pd.DataFrame,
                       osha: pd.DataFrame | None) -> tuple[pd.DataFrame,
                                                           list[dict]]:
    """Evaluate ``E_operating_by`` over a facility frame.

    Returns the frame with :data:`EDIT_COLUMNS` added and one dict per failing
    record. Diagnosis only -- what to DO with a failure is the caller's, which
    is why this never drops a row and never raises.
    """
    out = frame.copy()
    out["osha_operating_by"] = pd.Series([None] * len(out), index=out.index,
                                         dtype=object)
    out["open_date_falsified"] = False
    if osha is None or osha.empty or out.empty:
        return out, []

    bounds = _tightest_bounds(out, osha)
    failures: list[dict] = []
    for pos, (date, activity) in bounds.items():
        label = out.index[pos]
        out.at[label, "osha_operating_by"] = date
        claimed = out.at[label, "open_q_index"]
        if pd.isna(claimed) or _quarter_start(claimed) <= pd.Timestamp(date):
            continue
        out.at[label, "open_date_falsified"] = True
        start = _quarter_start(claimed)
        failures.append({
            "edit": "E_operating_by",
            "facility_id": str(out.at[label, "facility_id"])
            if "facility_id" in out.columns else str(label),
            "site_address": str(out.at[label, "site_address"])
            if "site_address" in out.columns else "",
            "claimed_open": f"{start.year}Q{(start.month - 1) // 3 + 1}",
            "claimed_open_q_index": float(claimed),
            "osha_operating_by": date,
            "osha_activity_nr": activity,
            "quarters_after_the_bound": int(
                claimed - (pd.Timestamp(date).year * 4
                           + (pd.Timestamp(date).month - 1) // 3)),
        })
    failures.sort(key=lambda f: f["facility_id"])
    return out, failures


def apply_operating_by(frame: pd.DataFrame, osha: pd.DataFrame | None,
                       disposition: str = REPORT,
                       label: str = "") -> tuple[pd.DataFrame, list[dict]]:
    """Check the edit and dispose of the failures as the caller asked.

    ``EXCLUDE`` removes the failing record; the original CSV is untouched and
    the returned report carries the value that was rejected, so the exclusion
    is reversible from the report alone.
    """
    out, failures = check_operating_by(frame, osha)
    where = f" in {label}" if label else ""
    if osha is None:
        _log.warning("E_operating_by NOT EVALUATED%s: %s is absent. The edit "
                     "is declared and unchecked, which is not the same as "
                     "passed.", where, edit_by_name("E_operating_by").source)
        return out, failures
    if not failures:
        _log.info("E_operating_by: %d facility record(s)%s checked against "
                  "OSHA, none falsified", len(out), where)
        return out, failures

    for f in failures:
        _log.warning(
            "E_operating_by FAILED%s: %s claims to have opened in %s but OSHA "
            "inspection %s proves the establishment at %s was operating on "
            "%s, %d quarter(s) earlier. The claimed date is impossible, not "
            "merely weaker. Disposition: %s.",
            where, f["facility_id"], f["claimed_open"], f["osha_activity_nr"],
            f["site_address"], f["osha_operating_by"],
            f["quarters_after_the_bound"], disposition)

    if disposition != EXCLUDE:
        _log.warning("%d record(s)%s fail E_operating_by and are REPORTED, "
                     "not excluded. Their falsified dates still set the "
                     "target.", len(failures), where)
        return out, failures
    return out[~out["open_date_falsified"]].reset_index(drop=True), failures
