"""Pull Amazon facilities out of the national OSHA inspection extract.

Why this source
---------------
Every other attempt to date last-mile facilities failed on coverage: press
releases exist only where a reporter cared, Google Maps merges listings with
previous tenants, and the one public network census (MWPVL) is frozen at
April 2012. OSHA is the first source that is *uniform* — every state, every
year, one schema, no dependence on local journalism.

What it can and cannot tell us
------------------------------
``open_date`` on an inspection is the date OSHA OPENED THE CASE, not the date
the building opened. Conflating the two would be a fabricated event. What an
inspection proves is that the establishment EXISTED AND WAS OPERATING on that
date, which is an upper bound on its opening — exactly the interval-censored
form the hazard model already accepts.

So the earliest inspection at an address is the strongest statement available
here: "open by <date>". It will never say "opened in 2019".

The selection bias, stated plainly
----------------------------------
OSHA inspects where people get hurt and where people complain. Fulfillment
centres are enormous, heavily automated and dangerous; delivery stations are
small and staffed largely by third-party DSP drivers who are not Amazon
employees. So this source over-represents fulfillment centres. In Illinois it
returned 20 inspections of which one was a delivery station. It is a good way
to EXPAND the frame and a poor way to complete it.

Classifying a facility
----------------------
The operating entity in the establishment name is a better signal than the
facility code, which has misled us three times (``DEN5`` reads as a delivery
station and is a sortation centre, because DEN is Denver's airport):

    "Amazon Logistics"            -> last-mile arm, delivery station
    "Amazon Fulfillment Services" -> fulfillment centre
    "Amazon.Com.Dedc LLC"         -> holding entity, tells you nothing

    python -m siting_atlas.ingest.osha path/to/inspection.zip
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

from ..common import paths
from ..common.address import normalise_address
from ..common.context import init_run
from ..common.linkage import LinkRecord
from ..common.linkage_group import link
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer
from .osha_archive import rows as archive_rows

__all__ = ["classify", "earliest_by_site", "extract", "is_amazon_retailer",
           "normalise_address"]

_log = get_logger("osha")

#: Cheap pre-filter on the raw line. Deliberately broad - the establishment
#: name is free text typed by an inspector, so the retailer appears as
#: "Amazon", "Amazon.Com Services Llc", "AMAZON DCXS" and worse.
NEEDLE = re.compile(r"amazon", re.IGNORECASE)

#: Amazon is a river, so plenty of unrelated firms are named after it. A bare
#: substring match swept in a Hawaii construction company, a Nevada masonry
#: firm, tree surgeons and a North Carolina textile division - about 170 of
#: 625 addresses. None of them are warehouses.
NOT_THE_RETAILER = re.compile(
    r"\b(construction|masonry|carpentry|framing|roofing|tree|landscap|"
    r"environmental|mills|textile|plumbing|electric|paving|drywall|"
    r"concrete|excavat|nursery|marine|realty|pest)\b", re.I)

#: Names that unambiguously belong to the retailer.
IS_THE_RETAILER = re.compile(
    r"amazon\s*(\.\s*com|com\b|\s+(logistics|fulfil|data|web|sort|delivery|"
    r"fresh|air|prime|dedc|dsp|go|grocery|robotics|studios))", re.I)

#: NAICS families a warehouse plausibly files under. Used only to rescue a
#: name we cannot otherwise place - never to override an obvious exclusion.
WAREHOUSE_NAICS = ("493", "492", "454", "4931", "4921")


def is_amazon_retailer(name: str, naics: str) -> bool:
    """Whether this establishment is Amazon the retailer, not a namesake.

    Three tests in order: an explicit trade name wins; an obvious other trade
    excludes; anything left is admitted only if it files under a warehousing
    or courier NAICS. That last rule is the judgement call - it keeps bare
    "AMAZON" rows that sit in 493110 and drops the ones that do not.
    """
    if IS_THE_RETAILER.search(name):
        return True
    if NOT_THE_RETAILER.search(name):
        return False
    return str(naics)[:3] in WAREHOUSE_NAICS

#: Operating entity -> facility type. Order matters; first match wins.
ENTITY_TYPE = (
    (re.compile(r"delivery\s*station", re.I), "DS"),
    (re.compile(r"sort(ation)?\s*(cent|cntr)", re.I), "SC"),
    (re.compile(r"fulfil?lment", re.I), "FC"),
    (re.compile(r"amazon\s+logistics", re.I), "DS"),
    (re.compile(r"fresh|whole\s*foods", re.I), "GROCERY"),
    (re.compile(r"air|prime\s*air", re.I), "AIR"),
)

WANT = ("activity_nr", "estab_name", "site_address", "site_city",
        "site_state", "site_zip", "open_date", "naics_code")


def classify(name: str) -> str:
    """Facility type from the establishment name, or '' when it is silent.

    Returns '' rather than guessing. A wrong type is worse than no type: it
    decides whether the row sets the model's target at all.
    """
    for pattern, kind in ENTITY_TYPE:
        if pattern.search(name):
            return kind
    return ""


#: Standardisation and matching used to live here, in a `_SUFFIX` dict and a
#: one-line `normalise_address()`, with a SECOND and different copy inlined
#: in `scripts/osha_amazon.py`. The tables disagreed, so the number of
#: distinct Amazon sites depended on which entry point you ran. Both are
#: gone: `common.address` standardises and `common.linkage` matches.
#: `normalise_address` is re-exported because documentation names it, but it
#: is a view onto the parse now, not the matching rule.



def extract(path: Path) -> list[dict]:
    """Every Amazon inspection row, as a list of dicts.

    The cheap substring test runs on the RAW LINE before any CSV parsing,
    because parsing four million rows to discard all but a few thousand is
    most of the runtime for none of the value.
    """
    rows, scanned, rejected = [], 0, []
    for fields, line in archive_rows(path):
        scanned += 1
        if not NEEDLE.search(line):
            continue
        try:
            values = next(csv.reader([line]))
        except csv.Error:
            continue
        # DOL ships UPPERCASE headers while its own metadata documents them in
        # lower case, so every lookup is folded rather than trusting either.
        # strict=False on purpose: a truncated or over-long row is a
        # publisher defect, not a reason to abort a 5-million-row scan.
        row = {k.strip().lower(): v
               for k, v in zip(fields, values, strict=False)}
        name = row.get("estab_name", "")
        if not NEEDLE.search(name):
            continue        # 'amazon' matched some other column
        if not is_amazon_retailer(name, row.get("naics_code", "")):
            rejected.append(name)
            continue
        rows.append({k: row.get(k, "") for k in WANT})

    _log.info("scanned %d inspections, matched %d Amazon rows (%.3f%%); "
              "rejected %d namesake establishments",
              scanned, len(rows), 100 * len(rows) / max(scanned, 1),
              len(rejected))
    if rejected:
        import collections as _c
        top = ", ".join(n for n, _ in _c.Counter(rejected).most_common(4))
        _log.debug("rejected examples: %s", top)
    return rows


def earliest_by_site(rows: list[dict]) -> list[dict]:
    """Collapse to one record per BUILDING, keeping the earliest inspection.

    The earliest inspection is the tightest 'operating by' bound the source
    can support; later ones add nothing.

    This used to group on an exact-string key, which meant two spellings of
    one address produced two buildings and the earlier date - the whole
    point of the collapse - was lost on one of them. It now groups on
    `linkage.link`, so "315 SHUKSAN WAY DWS4" and "315 SHUKSAN WAY" are one
    site while "1555 N CHRISMAN RD" and "1555 S CHRISMAN RD" remain two.

    A record the linker could not place unambiguously stays as its own
    group. That is the conservative direction on purpose: a spurious extra
    row is visible in the count and a wrong merge is not, because the
    facility it deleted never appears anywhere to be missed.
    """
    keep = [r for r in rows if normalise_address(r["site_address"])]
    recs = [
        LinkRecord.build(str(i), r["site_address"], r["site_city"],
                         r["site_state"], r["site_zip"])
        for i, r in enumerate(keep)
    ]
    grouping = link(recs)

    out = []
    for members in grouping.groups:
        group = [keep[i] for i in members]
        # Earliest inspection wins, and the facility types seen anywhere in
        # the group are pooled: one inspector's establishment name may
        # identify the type when the other's does not.
        group.sort(key=lambda r: r["open_date"][:10])
        seen = {k for k in (classify(r["estab_name"]) for r in group) if k}
        rec = dict(group[0])
        rec["facility_type"] = "/".join(sorted(seen))
        rec["operating_by"] = group[0]["open_date"][:10]
        rec["n_inspections"] = len(group)
        out.append(rec)
    out.sort(key=lambda r: (r["site_state"], r["site_city"],
                            r["operating_by"]))
    _log.info("%d rows -> %d distinct Amazon buildings "
              "(%d merged, %d pairs held for review)",
              len(keep), len(out), len(keep) - len(out),
              len(grouping.review))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("archive", help="inspection.zip, .csv or .csv.gz")
    ap.add_argument("--out", default=None)
    # The audit needs the rows BEFORE deduplication, or it has nothing to
    # measure: running it on the collapsed output only proves the output is
    # already collapsed. This flag is what makes the reported match rate
    # reproducible rather than a number quoted from a one-off session.
    ap.add_argument("--no-collapse", action="store_true",
                    help="write one row per inspection, for address_audit")
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()

    src = Path(args.archive).expanduser()
    if not src.exists():
        raise SystemExit(f"{src} not found")

    with traced_layer("L0", f"OSHA extract from {src.name}"):
        with step("osha:scan"):
            rows = extract(src)
            metric("osha_amazon_rows", len(rows))
        with step("osha:collapse"):
            sites = rows if args.no_collapse else earliest_by_site(rows)
            metric("osha_amazon_sites", len(sites))

    out = Path(args.out) if args.out else paths.INTERIM / "osha_amazon.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(sites[0]) if sites else WANT)
        wr.writeheader()
        wr.writerows(sites)
    artefact(out, rows=len(sites))

    by_type: dict[str, int] = defaultdict(int)
    by_state: dict[str, int] = defaultdict(int)
    for s in sites:
        by_type[s["facility_type"] or "(unlabelled)"] += 1
        by_state[s["site_state"]] += 1

    print(f"\n  {len(rows):,} Amazon inspections -> {len(sites):,} buildings")
    print(f"  -> {out}\n")
    for title, tally, limit in (("by facility type", by_type, None),
                                ("top states", by_state, 12)):
        print(f"  {title}")
        ranked = sorted(tally.items(), key=lambda kv: -kv[1])
        for k, v in ranked[:limit] if limit else ranked:
            print(f"    {k:16} {v:>5}")
    print("\n  matcher error rates: "
          "python -m siting_atlas.ingest.address_audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
