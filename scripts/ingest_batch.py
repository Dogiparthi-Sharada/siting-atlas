"""Join a labelling batch back to its worklist rows.

    python scripts/ingest_batch.py 2

The prompts deliberately carry no identifiers -- only plain addresses -- so
the answers come back numbered and nothing else. The join is therefore on
(batch, item) against UNLABELLED_WORKLIST.csv, and it is strict: a missing
or unparsable answer is reported, never silently dropped, because a silent
drop would look exactly like a site that is not a delivery station.
"""
from __future__ import annotations

import collections
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "collection" / "results"
WORKLIST = ROOT / "data" / "collection" / "prompts" / "UNLABELLED_WORKLIST.csv"

#: Gemini's wording -> the facility_type vocabulary in facility_check.py.
KIND = {"DELIVERY STATION": "DS", "FULFILLMENT CENTER": "FC",
        "SORTATION CENTER": "SC", "AIR HUB": "AIR", "FRESH": "GROCERY",
        "DATA CENTER": "OTHER", "OFFICE": "OTHER", "PHARMACY": "OTHER",
        "WHOLE FOODS": "OTHER", "OTHER": "OTHER", "UNKNOWN": ""}

LINE = re.compile(
    r"^\s*(\d+)\.\s*([A-Z][A-Z /]+?)\s*-\s*\"(.*?)\"\s*-\s*(\S+)")


def main(batch: str) -> int:
    raw = (RESULTS / f"UNLABELLED_BATCH_{batch}_RAW.txt").read_text("utf-8")
    answers = {}
    for line in raw.splitlines():
        m = LINE.match(line)
        if m:
            answers[int(m.group(1))] = (m.group(2).strip(), m.group(3).strip(),
                                        m.group(4))

    with open(WORKLIST, encoding="utf-8") as fh:
        work = [r for r in csv.DictReader(fh) if r["batch"] == batch]
    if not work:
        raise SystemExit(f"no worklist rows for batch {batch}")

    rows, tally, missing = [], collections.Counter(), []
    for r in work:
        item = int(r["item"])
        if item not in answers:
            missing.append(item)
        kind, evidence, url = answers.get(item, ("", "", ""))
        code = KIND.get(kind, "")
        # A blank facility_type has three causes and they are not the same
        # thing. UNKNOWN is an ANSWER -- the labeller looked and could not
        # tell -- and tallying it as "(unmatched)" reads as a join failure,
        # which is how four batch-3 rows came to be described as missing
        # data. A word this script prints is a word someone quotes.
        tally[code or kind or "(no answer)"] += 1
        rows.append({**r, "facility_type": code, "label": kind,
                     "evidence": evidence, "source_url": url})

    out = RESULTS / f"UNLABELLED_BATCH_{batch}_CLASSIFIED.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"  batch {batch}: parsed {len(answers)}/{len(work)} answers")
    if missing:
        print(f"  MISSING items (reported, not dropped): {missing}")
    for k, v in tally.most_common():
        print(f"      {k:12} {v:>3}")
    print(f"  -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "1"))
