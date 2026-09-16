"""L0 — the two TIGER/Line road layers the highway covariate is built from.

Two layers, because one of them does not contain the thing we want
------------------------------------------------------------------
``PRIMARYROADS`` is ONE national shapefile, 37 MB, every feature coded
``MTFCC=S1100``. It is the freeway and highway CENTRELINE network and it
is what a "distance to the nearest highway" measure is made of.

It does not contain ramps. Measured, not assumed: of its 17,458
features, exactly one has "Ramp" anywhere in ``FULLNAME`` and the MTFCC
column takes a single value. ``PRISECROADS`` adds ``S1200`` (secondary)
and no ramps either. TIGER publishes ramps as ``MTFCC=S1630`` and ships
them only in the per-COUNTY ``ROADS`` files — 3,234 of them nationally.

That matters because the siting constraint is not "near a freeway", it
is "near a freeway EXIT". A ZCTA can be straddled by eight lanes of
interstate for four miles with no way on or off it, and a
centreline-distance measure scores that ZCTA as perfectly served. So
both layers are fetched: the national file for the cheap measure, and
the county files, for the counties the choice model actually builds
choice sets in, for the real one.

Provenance, and why the county files are hashed in a sidecar
-------------------------------------------------------------
`common.http.fetch` appends one line to ``data/raw/manifest.jsonl`` per
download, which is right for a source that is one file and wrong for a
source that is 900. Nine hundred manifest lines would bury every other
source in it. The county layer therefore gets:

  * ``data/raw/tiger_roads/roads_sha256.txt`` — one
    ``<sha256>  <filename>`` line per county file, the format ``sha256sum
    -c`` reads, so a reviewer can verify every byte of every file;
  * ONE manifest line for the layer, whose ``sha256`` is the digest of
    that sidecar. The sidecar covers the files, the manifest covers the
    sidecar, and the chain is checkable end to end.

The national file goes through `fetch` unchanged and gets its own
ordinary manifest line.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

from ..common import context, paths
from ..common.http import USER_AGENT, fetch
from ..common.logging_setup import get_logger

_log = get_logger("ingest.tiger_fetch")

#: Pinned. A silent vintage change is the failure mode that corrupts a
#: panel without erroring, and `registry.py` pins every other TIGER pull
#: the same way. 2023 is the latest full release at the time of writing.
VINTAGE = "2023"
BASE = f"https://www2.census.gov/geo/tiger/TIGER{VINTAGE}"
PRIMARY_URL = f"{BASE}/PRIMARYROADS/tl_{VINTAGE}_us_primaryroads.zip"
COUNTY_URL = BASE + "/ROADS/tl_" + VINTAGE + "_{geoid}_roads.zip"

SOURCE = "tiger_roads"
RAW = paths.RAW / SOURCE
COUNTY_DIR = RAW / "roads"
SIDECAR = RAW / "roads_sha256.txt"

RETRIES = 3
BACKOFF = 3.0

#: Below this, the file on disk is not a shapefile archive. www2 answers a
#: burst of requests with HTTP 429 and a 247-byte HTML body, and `requests`
#: reports that as a successful download because it IS one — a successful
#: download of an error page. One slipped through a 900-county run and GDAL
#: reported it as "does not exist in the file system", which is an honest
#: error but not an obvious one. The smallest real county ROADS zip in this
#: run is 44 KB, so 20 KB separates the two cases with room to spare.
MIN_ZIP_BYTES = 20_000

#: Connecticut abolished its eight counties as statistical geography in
#: 2022 and the Census Bureau replaced them with nine COUNCIL OF
#: GOVERNMENTS planning regions. TIGER 2023 publishes ROADS under the new
#: codes and under none of the old ones, so a run asking for 09001-09015
#: gets eight 404s and silently loses Hartford, Bridgeport and New Haven
#: — three metros with delivery stations in them. The panel still carries
#: the old codes, so the substitution has to happen here.
#:
#: The mapping is not one-to-one and is deliberately not attempted: the
#: nine regions tile the same state as the eight counties, so requesting
#: ALL of them whenever ANY Connecticut county is asked for covers
#: everything the caller wanted and a little more. Over-covering costs a
#: few extra ramps in a neighbouring region and cannot lose any.
STATE_SUBSTITUTIONS = {
    "09": ("09110", "09120", "09130", "09140", "09150", "09160", "09170",
           "09180", "09190"),
}

__all__ = ["COUNTY_DIR", "PRIMARY_URL", "SIDECAR", "STATE_SUBSTITUTIONS",
           "VINTAGE", "county_roads", "primary_roads", "resolve_geoids"]


def resolve_geoids(geoids: list[str]) -> list[str]:
    """County codes as TIGER 2023 publishes them. See `STATE_SUBSTITUTIONS`."""
    out = set()
    for geoid in geoids:
        out.update(STATE_SUBSTITUTIONS.get(geoid[:2], (geoid,)))
    return sorted(out)


def primary_roads(force: bool = False) -> Path:
    """The national primary-road shapefile, cached and in the manifest."""
    got = fetch(PRIMARY_URL, source=SOURCE, force=force)
    _log.info("primary roads: %.1f MB, sha256 %s",
              got.bytes / 1e6, got.sha256[:12])
    return got.path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(url: str, target: Path) -> bool:
    """One county file, with retries. False when no file can be had.

    A 404 is a real answer here and not an error: TIGER does not publish
    a ROADS file for every FIPS code the panel carries (Connecticut's
    eight abolished counties are the big case; see
    `STATE_SUBSTITUTIONS`).

    A file that cannot be fetched after every retry is ALSO returned as
    False rather than raised. That is a deliberate trade and it is only
    safe because of `tiger_scope.mark_coverage`: an unfetched county
    makes its ZCTAs NULL on the interchange columns, which every
    consumer can see, so the failure degrades coverage visibly instead
    of either aborting a 900-county job or — far worse — writing zeros.

    It is not hypothetical. ``www2.census.gov`` sits behind a WAF that
    answered ``tl_2023_21145_roads.zip`` with HTTP 200 and a 247-byte
    "Request Rejected" page on every attempt over twenty minutes, from
    two user agents, while the adjacent county served normally. The file
    is in the directory listing. One county of 901 is not a reason to
    have no ramp layer.
    """
    for attempt in range(1, RETRIES + 1):
        try:
            with requests.get(url, headers={"User-Agent": USER_AGENT},
                              timeout=120, stream=True) as resp:
                if resp.status_code == 404:
                    return False
                resp.raise_for_status()
                tmp = target.with_suffix(".part")
                with open(tmp, "wb") as fh:
                    for chunk in resp.iter_content(1 << 16):
                        fh.write(chunk)
                size = tmp.stat().st_size
                if size < MIN_ZIP_BYTES:
                    tmp.unlink()
                    raise requests.RequestException(
                        f"{resp.status_code} returned {size} bytes for "
                        f"{target.name} — an error page, not a shapefile")
                tmp.replace(target)      # atomic: no half-written cache
                return True
        except requests.RequestException as exc:
            if attempt == RETRIES:
                _log.error("%s: giving up after %d attempts (%s). This "
                           "county's ZCTAs will carry ramp_coverage=False "
                           "and NULL interchange columns.",
                           target.name, RETRIES, exc)
                return False
            _log.warning("%s attempt %d/%d: %s", target.name, attempt,
                         RETRIES, exc)
            time.sleep(BACKOFF * attempt)
    return False


def _write_sidecar(files: dict[str, str]) -> str:
    """``sha256sum -c`` format, sorted, and the digest OF that file."""
    body = "".join(f"{sha}  {name}\n" for name, sha in sorted(files.items()))
    SIDECAR.write_text(body, encoding="utf-8")
    return hashlib.sha256(body.encode()).hexdigest()


def _manifest_line(record: dict) -> None:
    """Append, unless this exact content is already recorded.

    The manifest is append-only by design — `common.http` says so and it
    is right, because a provenance record that can be rewritten is not
    provenance. But an APPEND-ONLY log is not a licence to write the same
    line every run: rebuilding the covariate five times would leave five
    indistinguishable entries for one layer and a reviewer would have to
    guess which describes the bytes on disk. The guard is on the
    CONTENT HASH, so a real change to the layer still appends.
    """
    if paths.MANIFEST.exists():
        with open(paths.MANIFEST, encoding="utf-8") as fh:
            for line in fh:
                if (line.strip()
                        and json.loads(line).get("sha256")
                        == record["sha256"]):
                    _log.info("manifest already records sha256 %s",
                              record["sha256"][:12])
                    return
    with open(paths.MANIFEST, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def county_roads(geoids: list[str], force: bool = False) -> dict:
    """Every county ROADS zip for `geoids`, plus the provenance sidecar.

    Resumable by construction: a county already on disk is hashed and
    skipped, so an interrupted run costs only what it had not yet
    fetched. Returns the paths present and the counties TIGER has no
    file for.
    """
    COUNTY_DIR.mkdir(parents=True, exist_ok=True)
    wanted = resolve_geoids(sorted(set(geoids)))
    present: dict[str, Path] = {}
    shas: dict[str, str] = {}
    missing: list[str] = []
    fetched = 0
    for i, geoid in enumerate(wanted, 1):
        target = COUNTY_DIR / f"tl_{VINTAGE}_{geoid}_roads.zip"
        stale = target.exists() and target.stat().st_size < MIN_ZIP_BYTES
        if stale:
            _log.warning("%s is %d bytes — re-fetching", target.name,
                         target.stat().st_size)
            target.unlink()
        if not target.exists() or force:
            if not _download(COUNTY_URL.format(geoid=geoid), target):
                missing.append(geoid)
                continue
            fetched += 1
            if fetched % 50 == 0:
                _log.info("county roads: %d/%d fetched", i, len(wanted))
        present[geoid] = target
        shas[target.name] = _sha256(target)

    digest = _write_sidecar(shas)
    total = sum(p.stat().st_size for p in present.values())
    _manifest_line({
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "source": f"{SOURCE}_county",
        "url": COUNTY_URL.format(geoid="<county_geoid>"),
        "sha256": digest, "bytes": int(total),
        "path": paths.rel(SIDECAR), "run_id": context.run_id(),
        "note": (f"TIGER/Line {VINTAGE} per-county ROADS, {len(present)} "
                 f"counties — every county of the {len(geoids)} the choice "
                 "model builds choice sets in. Fetched for MTFCC=S1630 "
                 "(ramps), which the national PRIMARYROADS file does not "
                 "contain. sha256 here is the digest OF "
                 f"{paths.rel(SIDECAR)}, which carries one sha256 per "
                 "county file in sha256sum -c format; verify with "
                 f"`cd {paths.rel(COUNTY_DIR)} && sha256sum -c "
                 f"../{SIDECAR.name}`."),
    })
    _log.info("county roads: %d counties on disk (%d newly fetched, "
              "%d with no TIGER file), %.0f MB, sidecar sha256 %s",
              len(present), fetched, len(missing), total / 1e6, digest[:12])
    # What the CALLER asked for, expressed in the caller's own codes: a
    # Connecticut county is covered when its replacement regions are on
    # disk, and the crosswalk downstream still speaks in county codes.
    covered = {g for g in geoids
               if g in present
               or any(s in present
                      for s in STATE_SUBSTITUTIONS.get(g[:2], ()))}
    return {"paths": present, "missing": missing, "covered": sorted(covered),
            "sidecar_sha256": digest, "bytes": int(total)}
