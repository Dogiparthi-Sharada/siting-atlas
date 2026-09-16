#!/usr/bin/env python3
"""Pull Amazon rows out of the OSHA inspection extract.

    python3 scripts/osha_amazon.py inspection.zip [--out FILE]

This used to be a standalone stdlib-only copy of the ingest stage, with its
OWN `norm()` and its own street-suffix table. That table was a subset of the
one in `ingest/osha.py`: it knew AVENUE and ROAD but not CIRCLE, PLACE,
TERRACE, TRAIL, the diagonal directionals or the unit words, and it had no
Amazon-namesake filter at all. So the two entry points disagreed about how
many distinct Amazon sites exist in the same input file, and which answer
you got depended on which one you happened to run.

Two matchers that disagree is the defect this script was part of, so it no
longer contains a matcher. It is now a convenience launcher for the package
stage, which is the single implementation:

    python -m siting_atlas.ingest.osha inspection.zip

Keeping the launcher is deliberate - the path is referenced in the
provenance documentation and in shell history - but it must not be a second
opinion. To check what the matcher is doing, run the audit:

    python -m siting_atlas.ingest.address_audit --sweep
"""

import sys

from siting_atlas.ingest.osha import main

if __name__ == "__main__":
    sys.exit(main())
