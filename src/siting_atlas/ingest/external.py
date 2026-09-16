"""Validate manually-placed sources in ``data/external/``.

Several sources cannot be fetched from the build environment — the host
refuses the request, the provider requires a credential, or there is no
stable endpoint at all. Those arrive by hand, and this module answers one
question before the pipeline depends on them: *is what landed actually
usable?*

    python -m siting_atlas.ingest.external --check

Checks performed per source: the folder exists, a file matching the expected
pattern is present, it is readable, and — for the facility panel, which is
the target variable — that required columns exist and ZIP codes still carry
their leading zeros.
"""

from __future__ import annotations

import argparse
import zipfile
from dataclasses import dataclass
from pathlib import Path

from ..common import paths
from ..common.context import init_run
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import step, traced_layer

# Re-exported: the facility-panel rules moved to their own module for size,
# but callers and tests have always imported them from here.
from .facility_check import (
    FACILITY_OPTIONAL,
    FACILITY_REQUIRED,
    VALID_SOURCE_TYPES,
    VALID_STATUS,
    VALID_TYPES,
    _check_facility_panel,
)

_log = get_logger("external")

__all__ = ["check", "main", "FACILITY_REQUIRED", "FACILITY_OPTIONAL",
           "VALID_TYPES", "VALID_SOURCE_TYPES", "VALID_STATUS"]


@dataclass
class Expectation:
    """What a manually-placed source should look like on disk."""
    key: str
    patterns: tuple[str, ...]      # glob patterns, any one may match
    what: str                      # human description for the report
    min_bytes: int = 1024
    critical: bool = False         # pipeline cannot proceed without it


EXPECTED = (
    # `facilities.csv` is named explicitly, and first, because the folder
    # now also holds `national_facilities.csv` — a wider 70-row panel that
    # nothing in `src/` reads. Under the bare `*.csv` glob the "largest
    # match wins" rule below picked the national file (10KB) over the one
    # the warehouse actually loads (4.8KB), so the check reported a clean
    # bill of health for a file the pipeline never opens. Patterns are
    # tried in order, so the exact name wins and `*.csv` stays as the
    # fallback for a panel delivered under some other name.
    Expectation("facility_panel", ("facilities.csv", "*.csv"),
                "the target variable: facility openings", 200, critical=True),
    Expectation("zillow_zori", ("*zori*.csv", "*.csv"),
                "Zillow Observed Rent Index, ZIP grain", 1_000_000),
    Expectation("zillow_zhvi", ("*zhvi*.csv", "*.csv"),
                "Zillow Home Value Index, ZIP grain", 1_000_000),
    Expectation("ejscreen", ("*.csv.zip", "*.zip", "*.csv"),
                "EJScreen tract-level indicators", 1_000_000),
    Expectation("bls_oes", ("*.zip",),
                "BLS OES metropolitan wage tables", 1_000_000),
    Expectation("eia_prices", ("*.csv", "*.json"),
                "EIA regional energy prices", 500),
)


def _human(n: int) -> str:
    """Byte count as a short human string (e.g. "1.4MB"), for the report."""
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n}B"


def _find(exp: Expectation) -> Path | None:
    """The file satisfying an Expectation, or None.

    Patterns are tried in order and the LARGEST match wins, because an
    interrupted re-download leaves a short file beside the good one.
    """
    folder = paths.EXTERNAL / exp.key
    if not folder.is_dir():
        return None
    for pattern in exp.patterns:
        # TEMPLATE.csv ships with the repo as a schema example; treating it
        # as real data would let a run "succeed" on three fake rows.
        hits = [h for h in sorted(folder.glob(pattern))
                if h.name.upper() != "TEMPLATE.CSV"]
        if hits:
            return max(hits, key=lambda p: p.stat().st_size)
    return None


def _peek_archive(path: Path) -> dict:
    """Report what an archive contains without extracting it."""
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()[:6]
            return {"members": names, "member_count": len(zf.namelist())}
    except zipfile.BadZipFile:
        return {"error": "not a valid zip archive"}


def check() -> list[dict]:
    """Validate every expected manual source. Never raises."""
    results: list[dict] = []

    with traced_layer("L0", "validate manually-placed sources"):
        for exp in EXPECTED:
            with step(f"external:{exp.key}"):
                found = _find(exp)
                rec: dict = {"key": exp.key, "what": exp.what,
                             "critical": exp.critical}

                if found is None:
                    rec["status"] = "missing"
                    rec["hint"] = (f"place a file matching "
                                   f"{' or '.join(exp.patterns)} in "
                                   f"{paths.rel(paths.EXTERNAL / exp.key)}/")
                    level = _log.error if exp.critical else _log.warning
                    level("%-16s MISSING  %s", exp.key, rec["hint"])
                    results.append(rec)
                    continue

                size = found.stat().st_size
                rec.update(path=paths.rel(found), bytes=size,
                           size_human=_human(size))

                if size < exp.min_bytes:
                    rec["status"] = "suspect"
                    rec["errors"] = [
                        f"only {_human(size)}; expected at least "
                        f"{_human(exp.min_bytes)} — likely a truncated or "
                        f"placeholder download"]
                    _log.warning("%-16s SUSPECT  %s (%s)", exp.key,
                                 found.name, _human(size))
                    results.append(rec)
                    continue

                if found.suffix == ".zip":
                    rec["archive"] = _peek_archive(found)

                if exp.key == "facility_panel":
                    errs, warns, stats = _check_facility_panel(found)
                    rec.update(errors=errs, warnings=warns, stats=stats)
                    rec["status"] = "invalid" if errs else "ok"
                    if errs:
                        _log.error("%-16s INVALID  %s", exp.key, found.name)
                        for e in errs:
                            _log.error("%18s %s", "", e)
                    else:
                        _log.info("%-16s OK       %s (%s, %d rows)", exp.key,
                                  found.name, _human(size),
                                  stats.get("rows", 0))
                    for w in warns:
                        _log.warning("%18s %s", "", w)
                else:
                    rec["status"] = "ok"
                    _log.info("%-16s OK       %s (%s)", exp.key, found.name,
                              _human(size))

                results.append(rec)
    return results


def main() -> int:
    """CLI entry point. Returns 1 only if a CRITICAL source is unusable.

    The exit code is the contract: CI can gate on "is the target variable
    present" without parsing the report, while a missing optional source
    still prints but does not fail the build.
    """
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", default=True,
                    help="validate what is present (default)")
    ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()

    results = check()
    write_json(paths.METRICS / "external_check.json", {"results": results})

    ok = [r for r in results if r["status"] == "ok"]
    bad = [r for r in results if r["status"] in ("invalid", "suspect")]
    missing = [r for r in results if r["status"] == "missing"]
    blocking = [r for r in results if r["critical"] and r["status"] != "ok"]

    print(f"\n  {'source':18}{'status':10}{'detail'}")
    print(f"  {'-' * 66}")
    for r in results:
        detail = r.get("size_human", "")
        if r["status"] == "ok" and r["key"] == "facility_panel":
            s = r.get("stats", {})
            detail = (f"{s.get('rows', 0)} facilities, "
                      f"{s.get('year_range', '?')}, "
                      f"{len(s.get('operators', []))} operator(s)")
        elif r["status"] == "missing":
            detail = "not placed yet"
        flag = "!" if r["critical"] and r["status"] != "ok" else " "
        print(f" {flag}{r['key']:18}{r['status']:10}{detail}")

    print(f"\n  {len(ok)} ready | {len(bad)} need attention | "
          f"{len(missing)} not placed")
    if blocking:
        print("\n  BLOCKING: the facility panel is the target variable. "
              "Without it there is nothing to predict.")
        print("  See docs/data/ACQUISITION_GUIDE.md section 2.")
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
