"""Adjudicate facility rows that describe one building and disagree about it.

Rahm & Do separate *duplicated* records from *contradicting* records, and the
distinction decides the treatment. A duplicate you delete. A contradiction you
have to adjudicate, because deleting either row is a claim you cannot support.

What is in the data
-------------------
``common/linkage.py`` finds three pairs in
``data/external/facility_panel/national_facilities.csv`` at score 1.000, with
two correct non-matches and zero false positives. Identity is not in doubt —
the pairs differ only by abbreviation:

    NAT-0011 / NAT-0012  2815 W EL SEGUNDO BL / BLVD.   open 2020Q2 / 2017Q4
    NAT-0025 / NAT-0026  1500 E GRANT LINE / GRANTLINE  open 2025Q1 / 2026Q3
    NAT-0078 / NAT-0079  3610 NW SAINT HELENS / ST      open 2017Q4 / 2018Q3

Each pair disagrees about the **opening date** — by 10, 6 and 3 quarters — and
the opening date is the target variable. All six rows are
``source_type=permit, confidence=high``, so neither side of any pair is weaker
evidence than the other.

Why not just take the earlier one
---------------------------------
``enabled_flags`` aggregates with ``min(open_q_index)``, which is correct for
two *distinct* stations serving one ZIP — the ZIP is enabled from the earlier
of them — and wrong for two rows describing *one* station, where it is not an
aggregation at all but an unexamined tie-break that always resolves the same
way. Fellegi & Holt object to it three separate times:

1. It is an imputation rule specified independently of the edits, which is the
   practice their Criterion 2 exists to abolish — "it should not be necessary
   to specify imputation rules; they should derive automatically from the edit
   rules".
2. It is **directional**. ``min`` always resolves toward the earlier date, so
   it is biased early by construction on every conflicting pair. That is bias
   in the outcome, not noise, over ~170 ZCTA-quarters when the wider file is
   promoted.
3. Being directional it also violates Criterion 3, which asks that imputation
   maintain the frequency distribution of the variable. Taking the minimum
   shifts the whole opening-date distribution earlier.

The source semantics agree: a building permit is filed *before* the building
operates, so a permit date is a LOWER bound on the opening, and the minimum of
two lower bounds is the loosest one available. It switches a catchment on at
the earliest moment consistent with the evidence, labelling ZIP-quarters as
served when they may not have been — and false positives in the treated set
attenuate every hazard coefficient toward zero, the direction that makes a
null look like a finding.

What error localisation does and does not settle
------------------------------------------------
Fellegi & Holt's minimum-change criterion is often quoted as picking the
value. It does not. Corollary 2 identifies the smallest set of **fields** to
change and asserts that satisfying values exist. Here the failed edit is

    E_date :  (link_score >= STREET_MATCH)
              AND (open_q_index_A != open_q_index_B)

the two records agree on street, city, state, ZIP and geography and disagree
only on the date, so the minimal cover is the single field ``open_q_index``.
That is already more than ``min`` gives us — it records *that* a field was
adjudicated and which one. But §4's admissible set is uninformative: any value
with A == B satisfies the edit, so 2020Q2 and 2017Q4 are equally admissible.
The edits select the field. They do not select the date.

**§7 is what supplies the rest**: "where there is more than one minimal set of
fields, an a priori weight of the reliability of each field could easily be
used to select among [them] ... simply take the set with the lowest product of
a priori weights", with the worked intuition that a simple self-coded response
beats "the product of a complicated coding operation". For us the weight
attaches to the *provenance* of the date, which is what
:data:`DATE_RELIABILITY` declares.

Where the provenances **tie**, §1 option 2 applies and the paper says stop:
"one should, whenever possible, avoid 'manufacturing' data instead of
collecting it." So a tie is not resolved here. It is recorded as unresolved,
reported, and — in the file the build actually reads — made a hard failure, so
that a human does three permit lookups instead of a rule inventing a date.
All six rows of the three known pairs are ``source_type=permit,
confidence=high``, so all three tie and all three are human work.

The treatment
-------------
The pair collapses to one facility carrying both dates:

    open_q_index_lower       the earlier bound
    open_q_index_upper       the later bound
    open_q_index             the operative value: the more reliable source's
                             date when the sources differ, and NaN — not a
                             guess — when they tie
    open_date_contradicted   True when the two dates differ at all
    open_date_unresolved     True when they differ AND the sources tie
    open_date_resolved_by    "source_reliability" or "" — the audit trail
    duplicate_of             the facility_id(s) folded in

Nothing is deleted and nothing is edited: both original rows remain
recoverable from the CSV, and the collapse is reproducible by re-running the
matcher. Van den Broeck's requirement is that the original value is retained
and the edit is logged; here the "edit" is a grouping, and both the grouping
and the values it spans are in the output.

Scope today
-----------
``facilities.csv`` (43 rows, the file the pipeline actually reads) contains no
contradicting pair, so wiring this in changes no current number. The wider
``national_facilities.csv`` is read by nothing in ``src/`` — verified
2026-09-13 — so the "~170 ZCTA-quarters of target set by an unadjudicated
conflict" is what WOULD happen on the day that file is promoted, not what is
happening now. This module is the thing that stops it happening silently.
"""

from __future__ import annotations

import pandas as pd

from ..common.linkage import LinkRecord
from ..common.linkage_group import link
from ..common.logging_setup import get_logger

_log = get_logger("warehouse.facility_dedup")

#: Columns the adjudication adds. Every one is a bound, a flag or a record of
#: how a choice was made; none invents a value.
ADJUDICATED_COLUMNS = ("open_q_index_lower", "open_q_index_upper",
                       "open_date_contradicted", "open_date_unresolved",
                       "open_date_resolved_by", "duplicate_of")

#: Fellegi & Holt §7's a priori reliability weights, applied to the PROVENANCE
#: of an opening date rather than to a field. Most reliable first.
#:
#: This is not a new ranking. It is the order already declared in
#: ``ingest/facility_check.VALID_SOURCE_TYPES``, whose comment says the set is
#: "ordered loosely by how much weight a row deserves", read out as an
#: explicit rule so it can actually decide something. The date semantics
#: reinforce it rather than fight it: a press release dates the OPENING, a
#: permit is filed before the building operates and so only bounds it from
#: below, a job posting proves operation but not commencement, and
#: ``facility_check`` says of OSM outright "location only, never a date".
#:
#: A source_type not in this list, or absent, ranks last — an unknown
#: provenance cannot outrank a known one.
DATE_RELIABILITY = ("press_release", "permit", "news", "company_site",
                    "job_posting", "osm", "other")


def _rank(source_type) -> int:
    """Lower is more reliable. Unknown provenance sorts last."""
    key = str(source_type or "").strip().lower()
    return (DATE_RELIABILITY.index(key) if key in DATE_RELIABILITY
            else len(DATE_RELIABILITY))


def _records(frame: pd.DataFrame) -> list[LinkRecord]:
    """One LinkRecord per row, tolerating a file with no ``site_address``.

    An address-free file cannot be matched on anything but ZIP, and the
    comparator's three-valued slot logic already refuses to call that a match,
    so this degrades to "no pairs" rather than to "everything matches".
    """
    street = (frame["site_address"] if "site_address" in frame.columns
              else pd.Series("", index=frame.index))
    ids = (frame["facility_id"] if "facility_id" in frame.columns
           else pd.Series(frame.index.astype(str), index=frame.index))
    return [LinkRecord.build(str(rid), str(s or ""), str(c or ""),
                             str(st or ""), str(z or ""))
            for rid, s, c, st, z in zip(
                ids, street, frame.get("city", ""), frame.get("state", ""),
                frame.get("zcta", frame.get("zip", "")), strict=False)]


def adjudicate(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Collapse matched rows to one facility carrying an opening interval.

    Returns the frame with :data:`ADJUDICATED_COLUMNS` added and one report
    dict per collapsed group. Rows the matcher leaves alone keep
    ``open_q_index_lower == open_q_index == open_q_index_upper`` and
    ``open_date_contradicted = False``, so downstream code never has to branch
    on whether adjudication found anything.

    Diagnosis only. This function never raises: deciding that an unresolved
    contradiction should stop a build is the caller's job, and
    ``facility_load.load_facilities`` does it for the file the pipeline reads.
    """
    out = frame.copy()
    out["open_q_index_lower"] = out["open_q_index"]
    out["open_q_index_upper"] = out["open_q_index"]
    out["open_date_contradicted"] = False
    out["open_date_unresolved"] = False
    out["open_date_resolved_by"] = ""
    out["duplicate_of"] = pd.Series([None] * len(out), index=out.index,
                                    dtype=object)

    if len(out) < 2:
        return out, []

    groups = [g for g in link(_records(out)).groups if len(g) > 1]
    if not groups:
        return out, []

    ids = (out["facility_id"].astype(str).tolist()
           if "facility_id" in out.columns
           else [str(i) for i in range(len(out))])
    drop: list[int] = []
    report: list[dict] = []

    for group in groups:
        rows = out.iloc[group]
        span = rows["open_q_index"].dropna()
        keep, *rest = group
        lower, upper = (float(span.min()), float(span.max())) if len(span) \
            else (float("nan"), float("nan"))
        contradicted = bool(len(span) > 1 and upper > lower)
        value, resolved_by, winner = _resolve(rows, contradicted, lower)

        out.iloc[keep, out.columns.get_loc("open_q_index_lower")] = lower
        out.iloc[keep, out.columns.get_loc("open_q_index_upper")] = upper
        out.iloc[keep, out.columns.get_loc("open_date_contradicted")] = \
            contradicted
        out.iloc[keep, out.columns.get_loc("open_date_unresolved")] = \
            bool(contradicted and not resolved_by)
        out.iloc[keep, out.columns.get_loc("open_date_resolved_by")] = \
            resolved_by
        out.iloc[keep, out.columns.get_loc("open_q_index")] = value
        out.iloc[keep, out.columns.get_loc("duplicate_of")] = \
            ",".join(ids[i] for i in rest)
        drop.extend(rest)

        report.append({
            "facility_ids": [ids[i] for i in group],
            "open_q_index_lower": lower, "open_q_index_upper": upper,
            "quarters_apart": int(upper - lower) if contradicted else 0,
            "contradicted": contradicted,
            "unresolved": bool(contradicted and not resolved_by),
            "resolved_by": resolved_by,
            "source_types": sorted({str(s) for s in
                                    rows.get("source_type", pd.Series())}),
            "winner": winner})

    for entry in report:
        if entry["unresolved"]:
            _log.error(
                "UNRESOLVED contradicting facility records %s: the same "
                "building is dated %d quarters apart and both rows carry the "
                "same provenance (%s), so no a priori reliability weight "
                "separates them. The opening is bounded in [%g, %g] and "
                "open_q_index is left NaN rather than guessed. Resolve it by "
                "collection, not by rule — one permit lookup.",
                "/".join(entry["facility_ids"]), entry["quarters_apart"],
                ", ".join(entry["source_types"]) or "unknown",
                entry["open_q_index_lower"], entry["open_q_index_upper"])
        elif entry["contradicted"]:
            _log.warning(
                "contradicting facility records %s dated %d quarters apart; "
                "resolved to the %s row by a priori source reliability, "
                "opening bounded in [%g, %g]",
                "/".join(entry["facility_ids"]), entry["quarters_apart"],
                entry["winner"], entry["open_q_index_lower"],
                entry["open_q_index_upper"])
        else:
            _log.info("duplicate facility records %s agree on the opening "
                      "date; collapsed to one row",
                      "/".join(entry["facility_ids"]))

    return out.drop(index=out.index[drop]).reset_index(drop=True), report


def _resolve(rows: pd.DataFrame, contradicted: bool,
             lower: float) -> tuple[float, str, str]:
    """Pick the date only when provenance justifies it.

    Returns ``(open_q_index, resolved_by, winning source_type)``. On a tie the
    value is NaN: Fellegi & Holt §1 option 2 — "one should, whenever possible,
    avoid 'manufacturing' data instead of collecting it". A NaN here is not a
    lost event, because ``facility_load`` refuses to load a file that has one.
    """
    if not contradicted:
        return lower, "", ""

    dated = rows[rows["open_q_index"].notna()]
    ranks = dated.get("source_type", pd.Series(index=dated.index,
                                               dtype=object)).map(_rank)
    best = ranks.min()
    if (ranks == best).sum() != 1:
        return float("nan"), "", ""
    row = dated[ranks == best].iloc[0]
    return (float(row["open_q_index"]), "source_reliability",
            str(row.get("source_type", "")))
