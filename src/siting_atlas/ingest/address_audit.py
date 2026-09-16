"""Measure the address matcher instead of trusting it.

Why this file exists
--------------------
The previous matcher was never measured. There was no match rate, no error
rate, no threshold and no principle for choosing one, so "it works" meant
"the addresses I happened to look at came out right". Winkler RR99-04 §3.4
is blunt that measuring linkage error is the hard part - Belin and Rubin
(1995) is "currently the only method for automatically estimating record
linkage error rates", and it needs calibration data plus "substantial
separation of the curves of log frequency versus matching weight". We have
516 records, no calibration data, and a deterministic rule that emits no
weight distribution, so Belin-Rubin is unavailable and pretending otherwise
would be the same sin in a better suit.

What is available is the other half of Fellegi-Sunter's decision rule
(eq. 4): the band between LOWER and UPPER that exists precisely to be "held
for clerical review". Three things are therefore reported here, and all
three are counts of real pairs a human can open and check:

  1. MATCH RATE      - how far the extract collapses, and which pairs did it.
  2. BLOCKING RECALL - every match found by blocking, against every match
                       found by comparing all within-state pairs. This is
                       the false-negative source that no threshold can fix,
                       because a pair never generated is never judged.
  3. THE REVIEW BAND - listed in full, because at this scale "estimating"
                       the error rate by sampling would be silly when the
                       whole band is small enough to read.

    python -m siting_atlas.ingest.address_audit
    python -m siting_atlas.ingest.address_audit --sweep
"""

from __future__ import annotations

import argparse
import collections
import csv
import itertools
from pathlib import Path

from ..common import paths
from ..common.linkage import MATCH, REVIEW, LinkRecord, compare, jaro_winkler
from ..common.linkage_group import link


def load(path: Path) -> tuple[list[dict], list[LinkRecord]]:
    """Read the OSHA extract and parse every address once."""
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    recs = [
        LinkRecord.build(str(i), r.get("site_address", ""),
                         r.get("site_city", ""), r.get("site_state", ""),
                         r.get("site_zip", ""))
        for i, r in enumerate(rows)
    ]
    return rows, recs


def exhaustive(recs: list[LinkRecord]) -> dict[str, set]:
    """Compare every within-state pair, ignoring the blocking keys.

    This is the yardstick blocking is measured against. It is only feasible
    because n is 516; the point of computing it is to find out how much
    blocking costs BEFORE the dataset grows to where it cannot be computed.
    """
    out: dict[str, set] = {MATCH: set(), REVIEW: set()}
    for i, j in itertools.combinations(range(len(recs)), 2):
        if recs[i].state != recs[j].state:
            continue
        call = compare(recs[i], recs[j]).call
        if call in out:
            out[call].add((i, j))
    return out


def sweep(recs: list[LinkRecord]) -> list[tuple[float, int, list[str]]]:
    """Street-similarity distribution over pairs sharing a house number.

    The threshold constants in `common.linkage` were read off this. Printing
    it keeps them honest: if a future extract fills in the gap between the
    typo cluster and the different-street cluster, the cut stops being
    defensible and this is where that shows up first.
    """
    buckets: dict[float, list[str]] = collections.defaultdict(list)
    for i, j in itertools.combinations(range(len(recs)), 2):
        a, b = recs[i], recs[j]
        if a.state != b.state or not a.addr.street or not b.addr.street:
            continue
        if a.addr.number != b.addr.number:
            continue
        s = jaro_winkler(a.addr.core, b.addr.core)
        buckets[round(s, 2)].append(f"{a.addr.core}/{b.addr.core}")
    return [(k, len(v), v[:3]) for k, v in sorted(buckets.items(),
                                                  reverse=True)]


def _show_pair(rows, i, j, why, score) -> None:
    a, b = rows[i], rows[j]
    print(f"    {why}  (street similarity {score:.3f})")
    for r in (a, b):
        print(f"      {r['site_address'][:48]:50} "
              f"{r['site_city'][:18]:20} {r['site_zip']} {r['site_state']}")


def report(path: Path, do_sweep: bool = False) -> int:
    rows, recs = load(path)
    grouping = link(recs)
    n, k = len(recs), grouping.n_groups

    print(f"\n  ADDRESS LINKAGE AUDIT   {path}")
    print(f"  {'-' * 66}")
    print(f"  input rows                     {n:>6}")
    print(f"  distinct buildings after link  {k:>6}")
    print(f"  pairs merged                   {n - k:>6}")
    print(f"  match rate (rows collapsed)    {100 * (n - k) / n:>5.1f}%")

    full = exhaustive(recs)
    got = {p for p, v in grouping.verdicts.items() if v.call == MATCH}
    want = full[MATCH]
    print("\n  BLOCKING (the unrecoverable error source)")
    npairs = sum(1 for i, j in itertools.combinations(range(n), 2)
                 if recs[i].state == recs[j].state)
    print(f"    within-state pairs           {npairs:>6}")
    print(f"    pairs actually compared      {len(grouping.verdicts):>6}"
          f"   ({100 * len(grouping.verdicts) / npairs:.2f}%)")
    print(f"    matches found by blocking    {len(got & want):>6}"
          f" of {len(want)}")
    for i, j in sorted(want - got):
        print(f"      LOST: {rows[i]['site_address']}"
              f" | {rows[j]['site_address']}")

    print(f"\n  CLERICAL REVIEW BAND ({len(grouping.review)} pairs)")
    print("    Fellegi-Sunter eq. (4)'s middle region. These are not "
          "failures;\n    they are the pairs the evidence does not settle.")
    for i, j, v in grouping.review:
        _show_pair(rows, i, j, v.why, v.score)

    print(f"\n  AMBIGUOUS AFTER CONFLICT REPAIR ({len(grouping.ambiguous)})")
    print("    Records pulled out of a group that contradicted itself. "
          "Left\n    alone rather than attached to one side of the "
          "contradiction.")
    for i in grouping.ambiguous:
        print(f"      {rows[i]['site_address'][:48]:50} "
              f"{rows[i]['site_city'][:18]:20} {rows[i]['site_zip']}")

    if do_sweep:
        print("\n  STREET SIMILARITY SWEEP (pairs sharing a house number)")
        for score, count, examples in sweep(recs):
            print(f"    JW {score:.2f}  n={count:<4} {', '.join(examples)}")
    print()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default=None,
                    help="OSHA extract CSV (default: data/interim)")
    ap.add_argument("--sweep", action="store_true",
                    help="print the street-similarity distribution")
    args = ap.parse_args()
    src = (Path(args.input) if args.input
           else paths.INTERIM / "osha_amazon.csv")
    if not src.exists():
        raise SystemExit(f"{src} not found - run ingest.osha first")
    return report(src, args.sweep)


if __name__ == "__main__":
    raise SystemExit(main())
