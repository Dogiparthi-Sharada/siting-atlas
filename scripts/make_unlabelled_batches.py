"""Generate classification batches for the unlabelled OSHA buildings.

Why this exists
---------------
`ingest/osha.py` classifies a building from the establishment name, and the
name is free text typed by an inspector. For 362 of the 474 buildings it is
silent, so `classify()` correctly returns "" rather than guessing. That is
the right behaviour and it leaves 76% of the extract unusable: the model
fits 43 facilities while 362 sit unclassified on disk.

Labelling them is the single largest available increase in sample size, and
sample size is the binding constraint on the prediction model (38 usable
events against 5 parameters is 7.6 per parameter, under the floor of 10).

This script cuts the unlabelled set into batches sized for one sitting,
using the prompt wording already settled in `NATIONAL_BATCH_1.txt` — plain
addresses, no facility codes, quote-and-URL required, UNKNOWN allowed.

    python scripts/make_unlabelled_batches.py [--size 70]

Writes `data/collection/prompts/UNLABELLED_BATCH_<n>.txt` and one worklist
CSV carrying the identifiers, so answers can be joined back without the
prompt having to contain them.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "data" / "interim" / "osha_amazon.csv"
OUT = REPO / "data" / "collection" / "prompts"

#: The 10 pilot metros' states. Not a filter - a priority marker. A building
#: in a pilot state can enter the fitted panel immediately; one outside it
#: only helps once the national panel is wired.
PILOT_STATES = {"IL", "CO", "CA", "WA", "AZ", "NY", "NJ", "TX", "GA", "FL"}

PREAMBLE = """\
For each Amazon address below, tell me what KIND of facility it is.

Answer one line each:

  1. DELIVERY STATION - "quote naming the address" - https://url
  2. FULFILLMENT CENTER - "quote" - https://url
  3. UNKNOWN

The kinds:
  DELIVERY STATION   vans load here and drive to homes. 100,000-250,000 sq ft.
  SORTATION CENTER   sorts parcels between warehouses. No home delivery.
  FULFILLMENT CENTER stores inventory, picks orders. 600,000+ sq ft.
  AIR HUB / FRESH / OFFICE / DATA CENTER / OTHER

What works, in order - please actually try these:
  - the address in quotes with no mention of Amazon
  - the address plus "DSP" or "delivery service partner"
  - the address plus "square feet" (under 250,000 = delivery station,
    over 600,000 = fulfillment centre)
  - the address on hiring.amazon.com - the JOB TITLE gives it away
  - warehouse.ninja, zonhack, selleressentials, mapcarta, amazontours.com

Rules:
  - Quote a sentence naming the street or the city. Give the URL.
  - UNKNOWN if you cannot tell. Do not guess. Guessing the kind is worse than
    not knowing, because it decides whether the site counts at all.
  - OFFICE, DATA CENTRE, PHARMACY or WHOLE FOODS are useful answers, not
    failures - they tell me to exclude the site.
  - If it has CLOSED, say so with the year.

Every address is a real Amazon site from US Department of Labor OSHA
inspection records. The only question is which kind. The establishment name
on the inspection was too generic to tell (usually just "Amazon.com Services
LLC"), which is why these are unclassified rather than unverified.

Answer in the order given, numbered, one line each.

"""


def _already_known() -> set[tuple[str, str]]:
    """(normalised address, state) for every site the project has classified.

    THE BUG THIS EXISTS TO PREVENT, because it cost four evenings of the
    inspirator's time and returned thirteen facilities out of 362 sites.

    `unlabelled()` below selects OSHA rows whose `facility_type` is blank —
    rows the NAME-BASED regex in `ingest/osha.py` could not place. That is not
    the same predicate as "unknown to this project": a site the regex missed
    may already have been classified by hand and be sitting in
    `NATIONAL_CLASSIFIED.csv`, which is the file `national_facilities.csv` was
    built from. Measured after the fact: 289 of the 362 rows shipped, 80%,
    were already classified there.

    Unlabelled BY THE REGEX is not unknown TO THE PROJECT. The first version
    wrote the first while meaning the second, and nothing failed — the batches
    generated cleanly, the answers came back cleanly, and the duplication was
    invisible until somebody matched addresses.
    """
    known: set[tuple[str, str]] = set()
    for name, addr_col, state_col in (
            ("NATIONAL_CLASSIFIED.csv", "site_address", "state"),
            ("OSHA_CLASSIFIED.csv", "site_address", "site_state"),
            ("DS_PANEL.csv", "site_address", "state")):
        path = REPO / "data" / "collection" / "results" / name
        if not path.exists():
            continue
        with open(path, encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                addr = row.get(addr_col) or row.get("address") or ""
                state = row.get(state_col) or row.get("site_state") or ""
                if addr.strip():
                    known.add((_norm(addr), state.upper().strip()))
    for name in ("national_facilities.csv", "facilities.csv"):
        path = REPO / "data" / "external" / "facility_panel" / name
        if not path.exists():
            continue
        with open(path, encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                addr = (row.get("site_address") or "").strip()
                if addr:
                    known.add((_norm(addr),
                               (row.get("state") or "").upper().strip()))
    return known


def _norm(address: str) -> str:
    """Address reduced to letters, digits and single spaces, for matching.

    Deliberately crude. This is a DUPLICATE SCREEN, not the record linker —
    `common/linkage.py` does the careful version. Here a false positive costs
    one site not being asked about, and a false negative costs an evening, so
    the screen is tuned to over-exclude.
    """
    return re.sub(r"[^A-Z0-9 ]", " ", str(address).upper()).strip()


def unlabelled(path: Path) -> list[dict]:
    """Buildings the name-based classifier could not place, priority first."""
    known = _already_known()
    with open(path, encoding="utf-8") as fh:
        raw = [r for r in csv.DictReader(fh) if not r.get("facility_type")]
    rows = [r for r in raw
            if (_norm(r["site_address"]),
                r["site_state"].upper().strip()) not in known]
    dropped = len(raw) - len(rows)
    if dropped:
        _msg = (f"  {dropped} of {len(raw)} regex-unlabelled sites are "
                f"ALREADY classified elsewhere and were dropped")
        print(_msg)
    # Pilot states first so the earliest batches can feed the fitted panel
    # without waiting for the national wiring; then grouped by state and city
    # so a batch is geographically coherent and easier to research in one go.
    rows.sort(key=lambda r: (r["site_state"] not in PILOT_STATES,
                             r["site_state"], r["site_city"],
                             r["site_address"]))
    return rows


def write_batches(rows: list[dict], size: int,
                  prefix: str = "UNLABELLED") -> list[Path]:
    """One prompt file per batch, plus a worklist joining answers back."""
    OUT.mkdir(parents=True, exist_ok=True)
    written = []

    for start in range(0, len(rows), size):
        chunk = rows[start:start + size]
        n = start // size + 1
        pilot = sum(r["site_state"] in PILOT_STATES for r in chunk)
        lines = [PREAMBLE.rstrip(), ""]
        for i, r in enumerate(chunk, 1):
            city = r["site_city"].strip() or "unknown city"
            lines.append(f"{i:>3}. {r['site_address'].strip()}, "
                         f"{city}, {r['site_state']} {r['site_zip'].strip()}")
        path = OUT / f"{prefix}_BATCH_{n}.txt"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(path)
        print(f"  {path.name:26} {len(chunk):>3} sites "
              f"({pilot} in pilot states)")

    work = OUT / f"{prefix}_WORKLIST.csv"
    with open(work, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["batch", "item", "site_address", "site_city",
                    "site_state", "site_zip", "operating_by",
                    "n_inspections", "estab_name"])
        for start in range(0, len(rows), size):
            for i, r in enumerate(rows[start:start + size], 1):
                w.writerow([start // size + 1, i, r["site_address"],
                            r["site_city"], r["site_state"], r["site_zip"],
                            r.get("operating_by", ""),
                            r.get("n_inspections", ""),
                            r.get("estab_name", "")])
    print(f"  {work.name:26} {len(rows)} rows, for joining answers back")
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--size", type=int, default=70,
                    help="sites per batch (default 70, the size already used)")
    ap.add_argument("--prefix", default="UNLABELLED",
                    help="filename prefix. CHANGE IT for a new round: the "
                         "default would overwrite the batches already "
                         "answered, and their worklist is what joins the "
                         "answers back to the addresses")
    ap.add_argument("--force", action="store_true",
                    help="overwrite existing files with this prefix")
    args = ap.parse_args()

    if not SRC.exists():
        raise SystemExit(f"{SRC} not found - run the OSHA ingest first")
    existing = sorted(OUT.glob(f"{args.prefix}_BATCH_*.txt"))
    if existing and not args.force:
        raise SystemExit(
            f"\n  {len(existing)} file(s) already exist with prefix "
            f"'{args.prefix}':\n"
            + "".join(f"      {p.name}\n" for p in existing[:4])
            + (f"      ... and {len(existing) - 4} more\n"
               if len(existing) > 4 else "")
            + "\n  Overwriting them would ALSO overwrite "
              f"{args.prefix}_WORKLIST.csv, which is the only thing joining\n"
              "  the answers you already have back to their addresses.\n"
              "  Use --prefix ROUND2 for a new round, or --force if you "
              "really mean it.\n")
    rows = unlabelled(SRC)
    pilot = sum(r["site_state"] in PILOT_STATES for r in rows)
    print(f"\n  {len(rows)} unlabelled buildings "
          f"({pilot} in pilot states, {len(rows) - pilot} elsewhere)\n")
    write_batches(rows, args.size, args.prefix)
    print("\n  Paste one batch at a time. Answers go in "
          "data/collection/results/.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
