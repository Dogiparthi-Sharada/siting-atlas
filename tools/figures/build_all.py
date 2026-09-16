"""Build every proposal figure as a print-ready PNG.

    python tools/figures/build_all.py [--out docs/figures]

Palette and style tokens live in common.py and were validated against a white
print surface -- see the module docstring there for the validator output.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import apply_style          # noqa: E402
import fig_architecture                 # noqa: E402
import fig_methods                      # noqa: E402
import fig_evaluation                   # noqa: E402
import fig_backtest                     # noqa: E402
import fig_impact                       # noqa: E402

MODULES = [fig_architecture, fig_methods, fig_evaluation, fig_backtest,
           fig_impact]


def main() -> int:
    """Rebuild every figure and print what was written."""
    ap = argparse.ArgumentParser(description=__doc__)
    default = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..",
        "docs", "figures")
    ap.add_argument("--out", default=os.path.normpath(default))
    args = ap.parse_args()

    apply_style()
    print(f"Building figures -> {args.out}")
    print("-" * 67)

    built, failed = [], []
    t0 = time.time()
    for mod in MODULES:
        print(f"{mod.__name__}:")
        for builder in mod.BUILDERS:
            try:
                built.append(builder(args.out))
            except Exception as exc:                     # keep going
                failed.append((builder.__name__, exc))
                print(f"  FAILED {builder.__name__}: {exc}")

    print("-" * 67)
    total = sum(os.path.getsize(p) for p in built) / 1e6
    print(f"{len(built)} figure(s), {total:.1f} MB, {time.time() - t0:.1f}s")
    if failed:
        print(f"{len(failed)} FAILED:")
        for name, exc in failed:
            print(f"  {name}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
