"""Pull Amazon worksites out of the NLRB case-search export.

Why this source
---------------
Not for the rows. It is here to give the project a DENOMINATOR. Until now we
could say our facility panel was incomplete and could not say by how much,
because we had one list and no way to measure what a single list misses. Two
incomplete lists of the same population measure each other. That is the whole
argument for this file; the handful of extra places it contributes is a
by-product. `ingest.nlrb_capture` does the measuring.

What it can and cannot tell us
------------------------------
``Date Filed`` is the date a charge or petition was DOCKETED, not the date
the building opened. What a filing proves is that Amazon was OPERATING AT
THAT PLACE on that date, which is an upper bound on the opening - the same
interval-censored form OSHA gives, and it plugs into the same machinery. It
will never say "opened in 2019".

**There is no street address in this export, and that is the binding
limitation.** The finest grain the source supports is CITY + STATE. So every
statement built on it is about *cities that contain at least one Amazon
facility*, never about buildings. OSHA averages 1.39 buildings per city on
the current extract, so city coverage is NOT building coverage and the two
must not be quoted as if they were. Route B of `data/external/nlrb/HOWTO.md`
(the monthly election spreadsheets) does carry street addresses; the file we
hold is Route A and does not.

The selection bias, stated plainly
----------------------------------
NLRB cases arise where workers ORGANISE or where a worker is wronged enough
to file. That is not a random sample of buildings, and it is selective on
exactly the covariate the project's cost argument turns on: unionisation
correlates with facility size, with urban density and with state labour law.
It is also enormously concentrated - 195 of 969 cases are Staten Island. So
this is a good way to EXPAND the frame and a poor way to complete it.

Three further limitations, carried from HOWTO.md section 4, and expanded in
`docs/data/NLRB.md`: the DSP problem (delivery-station drivers are employed
by Delivery Service Partners, separate legal employers, so a charge at a
delivery station may never name Amazon - and delivery stations are our
target); selection on density; and no opening dates, only upper bounds.

The employer field is typed by regional staff and is not standardised: 290
distinct spellings across 969 cases, from "Amazon.com Services LLC" down to
a bare "Amazon". We do not try to distinguish operating entities the way
`ingest.osha` does, because without an address there is nothing to attach
the distinction to.

    python -m siting_atlas.ingest.nlrb
"""

from __future__ import annotations

import argparse
import csv
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from ..common import paths
from ..common.context import init_run
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, metric, step, traced_layer
from .nlrb_names import is_amazon_employer, normalise_city
from .osha import NEEDLE

__all__ = ["RawPlace", "by_place", "is_amazon_employer", "normalise_city",
           "read_cases"]

_log = get_logger("nlrb")

#: Column headings in the case-search export, folded to lower case on read
#: because the site has changed their capitalisation before.
WANT = {
    "case type": "case_type",
    "region": "region",
    "case number": "case_number",
    "case name": "employer_name",
    "status": "status",
    "date filed": "date_filed",
    "date closed": "date_closed",
    "city": "city",
    "states & territories": "state",
    "employees on charge/petition": "employees",
    "union": "union",
}

#: A SOFT cutoff in Van den Broeck et al. (2005) Figure 2's sense: above it,
#: flag for diagnosis, never silently edit. `Employees on charge/petition` is
#: the project's only facility-size proxy and it is contaminated. 65 of 968
#: values exceed 100,000 and 53 are exactly 1,000,000, because a
#: national-scope charge against the Teamsters records Amazon's ENTIRE
#: workforce against one city. The modal value, 1,000, appears 86 times and
#: is also the median - a suspiciously round number that is a textbook
#: ERRONEOUS INLIER, perfectly plausible for a fulfilment centre and almost
#: certainly a default. The field is carried through because it is all we
#: have; it is counted against this cutoff so that nobody uses it without
#: seeing the problem, and it is not truncated, because the largest US
#: fulfilment centres genuinely run to five figures.
EMPLOYEES_SOFT_CUTOFF = 20_000


def _iso(value: str) -> str:
    """NLRB prints MM/DD/YYYY. Return ISO, or '' rather than a wrong date."""
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except (ValueError, AttributeError):
            continue
    return ""


def _int(value: str) -> int | None:
    try:
        return int(float(str(value).replace(",", "").strip()))
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class RawPlace:
    """One city+state with at least one Amazon case, and what it supports.

    `operating_by` is the deliverable: the earliest filing at this place, an
    upper bound on when Amazon started operating there. `employees_*` is the
    only facility-size proxy this project has from any source, and it comes
    with two companions rather than alone: `n_with_employees`, because a
    median over two of eleven cases and one over eleven of eleven are not
    the same claim, and `n_employees_over_cutoff`, because some of the
    values are the company's headcount and not the site's.
    """

    city: str
    state: str
    operating_by: str = ""
    latest_filed: str = ""
    n_cases: int = 0
    n_unfair_labour: int = 0
    n_petition: int = 0
    n_with_employees: int = 0
    n_employees_over_cutoff: int = 0
    employees_max: int | None = None
    employees_median: float | None = None
    first_case_number: str = ""
    n_employer_spellings: int = 0
    regions: tuple[str, ...] = field(default_factory=tuple)

    @property
    def key(self) -> tuple[str, str]:
        return (self.city, self.state)

    def as_row(self) -> dict:
        row = {k: v for k, v in self.__dict__.items() if k != "regions"}
        row["regions"] = "|".join(self.regions)
        return row


def read_cases(path: Path) -> list[dict]:
    """Every Amazon case in the export, one dict per case.

    Parsed with `csv.DictReader` rather than by scanning lines: the
    Allegations column contains embedded newlines, so 970 records occupy
    7,890 physical lines and any line-oriented reader silently loses most
    of them.
    """
    rows, rejected = [], []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for raw in reader:
            folded = {(k or "").strip().lower(): (v or "")
                      for k, v in raw.items()}
            name = folded.get("case name", "")
            if not NEEDLE.search(name):
                continue
            if not is_amazon_employer(name):
                rejected.append(name)
                continue
            row = {dest: folded.get(src, "").strip()
                   for src, dest in WANT.items()}
            row["date_filed"] = _iso(row["date_filed"])
            row["date_closed"] = _iso(row["date_closed"])
            row["city_key"] = normalise_city(row["city"])
            row["state"] = row["state"].upper()
            rows.append(row)
    _log.info("%d Amazon NLRB cases; %d rejected as namesakes; "
              "%d distinct city+state", len(rows), len(rejected),
              len({(r["city_key"], r["state"]) for r in rows}))
    undated = sum(1 for r in rows if not r["date_filed"])
    if undated:
        _log.warning("%d cases have no parseable Date Filed", undated)
    return rows


def by_place(rows: list[dict]) -> list[RawPlace]:
    """Collapse to one record per city+state, keeping the earliest filing.

    Cases with no city or no state are DROPPED and counted, not assigned to
    a placeholder. A place we cannot name cannot be matched against OSHA,
    so carrying it would only pad the NLRB list on one side of a
    capture-recapture table and bias the answer.
    """
    groups: dict[tuple[str, str], list[dict]] = {}
    dropped = 0
    for row in rows:
        if not row["city_key"] or not row["state"]:
            dropped += 1
            continue
        groups.setdefault((row["city_key"], row["state"]), []).append(row)

    places = []
    for (city, state), group in groups.items():
        dated = sorted(r["date_filed"] for r in group if r["date_filed"])
        sizes = [n for n in (_int(r["employees"]) for r in group)
                 if n is not None]
        first = min(group, key=lambda r: r["date_filed"] or "9999")
        places.append(RawPlace(
            city=city, state=state,
            operating_by=dated[0] if dated else "",
            latest_filed=dated[-1] if dated else "",
            n_cases=len(group),
            n_unfair_labour=sum(1 for r in group
                                if r["case_type"].upper() == "C"),
            n_petition=sum(1 for r in group
                           if r["case_type"].upper() == "R"),
            n_with_employees=len(sizes),
            n_employees_over_cutoff=sum(1 for n in sizes
                                        if n > EMPLOYEES_SOFT_CUTOFF),
            employees_max=max(sizes) if sizes else None,
            employees_median=statistics.median(sizes) if sizes else None,
            first_case_number=first["case_number"],
            n_employer_spellings=len({r["employer_name"] for r in group}),
            regions=tuple(sorted({r["region"] for r in group if r["region"]})),
        ))
    places.sort(key=lambda p: (p.state, p.city))
    if dropped:
        _log.warning("%d cases dropped for a missing city or state", dropped)
    _log.info("%d cases -> %d distinct Amazon city+state places",
              len(rows), len(places))
    return places


def main() -> int:
    ap = argparse.ArgumentParser(description="NLRB Amazon case ingest")
    ap.add_argument("cases", nargs="?",
                    default=str(paths.EXTERNAL / "nlrb" /
                                "nlrb_cases_amazon.csv"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()

    src = Path(args.cases).expanduser()
    if not src.exists():
        raise SystemExit(f"{src} not found - see data/external/nlrb/HOWTO.md")

    with traced_layer("L0", f"NLRB extract from {src.name}"):
        with step("nlrb:read"):
            rows = read_cases(src)
            metric("nlrb_amazon_cases", len(rows))
        with step("nlrb:collapse"):
            places = by_place(rows)
            metric("nlrb_amazon_places", len(places))

    out = Path(args.out) if args.out else paths.INTERIM / "nlrb_amazon.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = list(places[0].as_row()) if places else ["city", "state"]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(p.as_row() for p in places)
    artefact(out, rows=len(places))

    print(f"\n  {len(rows):,} Amazon NLRB cases -> {len(places):,} places")
    print(f"  -> {out}\n")
    print("  coverage estimate: python -m siting_atlas.ingest.nlrb_capture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
