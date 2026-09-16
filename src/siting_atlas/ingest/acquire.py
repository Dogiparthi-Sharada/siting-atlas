"""L0 — acquire every reachable source into the content-addressed cache.

Run:

    python -m siting_atlas.ingest.acquire              # everything reachable
    python -m siting_atlas.ingest.acquire --only cbp_zip gaz_zcta
    python -m siting_atlas.ingest.acquire --force      # ignore the cache

What this stage guarantees
--------------------------
* nothing is downloaded twice — the cache key is the request identity;
* every fetch is appended to ``data/raw/manifest.jsonl`` with its SHA-256, so
  a reviewer can re-download and verify;
* a source that cannot be acquired is reported with the reason and the
  remediation, never skipped in silence.

Large sources are gated behind ``--include-large`` so a default run stays in
the tens of megabytes.
"""

from __future__ import annotations

import argparse

from ..common import config, paths
from ..common.context import init_run
from ..common.http import api_key, fetch
from ..common.log_json import write_json
from ..common.logging_setup import configure, get_logger
from ..common.trace import artefact, step, traced_layer
from .sources import ANALYTICAL, SOURCES, Availability, Source, get

_log = get_logger("acquire")

# Vintages are pinned per source rather than defaulted to "latest": a silent
# vintage change is the failure mode that corrupts a panel without erroring.
# Note the publishers disagree with each other - CBP files the 2022 reference
# year under /2022/zbp22totals.zip, while the Gazetteer publishes a 2023
# edition - so a single global year would be wrong for at least one of them.
VINTAGE_DEFAULT = {"year": "2023", "yy": "23", "state": "california"}
VINTAGE_BY_SOURCE = {
    "cbp_zip":    {"year": "2022", "yy": "22"},   # reference year 2022
    "gaz_zcta":   {"year": "2023"},
    "acs5":       {"year": "2023"},
    "acs1":       {"year": "2023"},
}

# Sources measured in hundreds of megabytes; opt-in only.
LARGE = {"tiger_zcta", "osm"}


def _resolve(url: str, key: str = "") -> str:
    """Substitute vintage placeholders, honouring per-source overrides."""
    subs = {**VINTAGE_DEFAULT, **VINTAGE_BY_SOURCE.get(key, {})}
    out = url
    for name, value in subs.items():
        out = out.replace("{" + name + "}", value)
    return out


def _skip_reason(src: Source, include_large: bool) -> str | None:
    """Why this source cannot be fetched now, or None if it can."""
    if src.handled_by:
        return f"acquired by `python -m {src.handled_by}`, not by a plain GET"
    if src.availability is Availability.MANUAL:
        return (f"no stable endpoint — place the file in "
                f"{paths.rel(paths.EXTERNAL)} (see docs/data/{src.key}.md)")
    if src.availability is Availability.BLOCKED:
        return (f"refused by this network — download manually and place in "
                f"{paths.rel(paths.EXTERNAL)}")
    if src.availability is Availability.NEEDS_KEY:
        if not src.key_env:
            return ("requires a credential, but no environment "
                    "variable is declared")
        if not api_key(src.key_env):
            return (f"needs ${src.key_env}; free key at "
                    f"{src.docs_url or 'the provider'}")
        return None
    if src.key in LARGE and not include_large:
        return "large download — re-run with --include-large"
    return None


def acquire_one(src: Source, force: bool = False) -> dict:
    """Fetch one source, or every declared vintage of it."""
    if src.vintages:
        return _acquire_vintages(src, force)
    url = _resolve(src.url, src.key)
    params = None
    if src.availability is Availability.NEEDS_KEY:
        params = {"key": api_key(src.key_env)}

    # The Census API answers a missing key with an HTML page and HTTP 200,
    # so anything expecting structured data asserts on Content-Type.
    expect = None
    if "api.census.gov" in url:
        expect = "json"

    got = fetch(url, source=src.key, params=params, force=force, expect=expect)
    artefact(got.path, source=src.key, sha256=got.sha256[:12],
             cached=got.from_cache)
    return {"key": src.key,
            "status": "cached" if got.from_cache else "fetched",
            "path": paths.rel(got.path), "bytes": got.bytes,
            "sha256": got.sha256}


def _acquire_vintages(src: Source, force: bool) -> dict:
    """Fetch a series published as one file per year.

    Each vintage lands in the same cache folder under its own content hash,
    so the normaliser can concatenate whatever is present.
    """
    got_bytes, fetched, cached = 0, 0, 0
    for vintage in src.vintages:
        url = (src.url.replace("{yy}", vintage)
                      .replace("{year}", f"20{vintage}"))
        got = fetch(url, source=src.key, force=force)
        got_bytes += got.bytes
        cached += got.from_cache
        fetched += not got.from_cache
    _log.info("%-20s %d vintage(s): %d fetched, %d cached, %.1f MB",
              src.key, len(src.vintages), fetched, cached, got_bytes / 1e6)
    return {"key": src.key, "status": "cached" if not fetched else "fetched",
            "vintages": list(src.vintages), "bytes": got_bytes}


def acquire(keys: list[str] | None = None, *, force: bool = False,
            include_large: bool = False) -> list[dict]:
    """Acquire the requested sources, or every analytical source by default."""
    targets = [get(k) for k in keys] if keys else list(ANALYTICAL)
    results: list[dict] = []

    with traced_layer("L0", f"acquire {len(targets)} source(s)"):
        for src in targets:
            with step(f"acquire:{src.key}"):
                reason = _skip_reason(src, include_large)
                if reason:
                    _log.warning("%-20s SKIP  %s", src.key, reason)
                    results.append({"key": src.key, "status": "skipped",
                                    "reason": reason})
                    continue
                try:
                    results.append(acquire_one(src, force=force))
                except Exception as exc:                  # noqa: BLE001
                    _log.error("%-20s FAIL  %s", src.key, exc)
                    results.append({"key": src.key, "status": "failed",
                                    "reason": str(exc)[:200]})

    done = [r for r in results if r["status"] in ("fetched", "cached")]
    total_mb = sum(r.get("bytes", 0) for r in done) / 1e6
    _log.info("acquired %d/%d source(s), %.1f MB on disk",
              len(done), len(results), total_mb)
    return results


def main() -> int:
    """CLI entry point for L0. Downloads the registry into data/raw/.

    Returns 0 always: a blocked or key-less source is a documented state
    reported in the table, and the pipeline is designed to run on whatever
    did arrive. Use ``ingest.external --check`` for the blocking verdict.
    """
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", nargs="*", metavar="KEY",
                    help="acquire only these source keys")
    ap.add_argument("--force", action="store_true",
                    help="re-download even if cached")
    ap.add_argument("--include-large", action="store_true",
                    help=f"also fetch {', '.join(sorted(LARGE))}")
    ap.add_argument("--list", action="store_true",
                    help="print the registry and exit")
    args = ap.parse_args()

    paths.ensure_dirs()
    # Before anything reads os.environ. `http.api_key` checks the environment
    # directly, so without this a default run reports "needs $CENSUS_API_KEY"
    # while the key sits in .env — the keyed sources worked only because
    # census_api and eia_api load it themselves.
    config.load_dotenv()
    init_run()
    configure()

    if args.list:
        print(f"\n  {'key':20}{'availability':13}{'grain':14}role")
        for s in SOURCES:
            print(f"  {s.key:20}{s.availability.value:13}"
                  f"{s.grain.value:14}{s.role[:44]}")
        return 0

    results = acquire(args.only, force=args.force,
                      include_large=args.include_large)
    write_json(paths.METRICS / "acquire_report.json", {"results": results})

    fetched = sum(1 for r in results if r["status"] == "fetched")
    cached = sum(1 for r in results if r["status"] == "cached")
    skipped = [r for r in results if r["status"] == "skipped"]
    failed = [r for r in results if r["status"] == "failed"]

    print(f"\n  fetched {fetched} | cached {cached} | "
          f"skipped {len(skipped)} | failed {len(failed)}")
    for r in skipped + failed:
        print(f"    {r['key']:20} {r['reason'][:88]}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
