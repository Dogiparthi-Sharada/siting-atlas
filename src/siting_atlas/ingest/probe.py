"""Reachability probe for every registered source.

Answers one question honestly: from *this* machine, right now, which sources
can the pipeline actually acquire? Run it before a build so a four-hour run
does not fail at minute 200 on a blocked host.

    python -m siting_atlas.ingest.probe

A HEAD or short ranged GET is used so probing costs kilobytes, not gigabytes.
Results are written to outputs/metrics/source_probe.json and are what the
per-source documents in docs/data/ are generated from.
"""

from __future__ import annotations

import argparse
import time
from datetime import date

import requests

from ..common import paths
from ..common.context import init_run
from ..common.http import USER_AGENT, _redact
from ..common.logging_setup import configure, get_logger
from ..common.trace import step, traced_layer
from .sources import SOURCES, Source

_log = get_logger("probe")

PROBE_TIMEOUT = 25
# Substituted into templated URLs so the probe hits a real file.
DEFAULTS = {"year": "2022", "yy": "22", "state": "california"}


def _resolve(url: str) -> str:
    """Fill template placeholders with concrete, known-good values."""
    out = url
    for k, v in DEFAULTS.items():
        out = out.replace("{" + k + "}", v)
    return out


def probe_one(src: Source) -> dict:
    """Probe a single source. Never raises — a failure is a result."""
    result = {
        "key": src.key,
        "declared": src.availability.value,
        "url": "",
        "status": None,
        "bytes": None,
        "content_type": "",
        "seconds": None,
        "verdict": "",
        "detail": "",
    }

    if not src.url:
        result["verdict"] = "manual"
        result["detail"] = "no stable endpoint; file placed by hand"
        return result

    url = _resolve(src.probe_url or src.url)
    result["url"] = _redact(url)
    t0 = time.perf_counter()
    try:
        # Range-limited GET: HEAD is unreliable on several Census paths.
        resp = requests.get(
            url, timeout=PROBE_TIMEOUT, stream=True,
            headers={"User-Agent": USER_AGENT, "Range": "bytes=0-2047"},
        )
        body = next(resp.iter_content(2048), b"") or b""
        result["status"] = resp.status_code
        result["bytes"] = len(body)
        result["content_type"] = resp.headers.get("Content-Type", "")
        result["seconds"] = round(time.perf_counter() - t0, 2)

        looks_html = b"<html" in body[:400].lower()
        if resp.status_code in (200, 206) and not looks_html:
            result["verdict"] = "open"
        elif resp.status_code in (200, 206) and looks_html:
            # A 200 carrying HTML is how the Census API reports a missing key.
            result["verdict"] = "needs_key"
            result["detail"] = ("HTML body on a 200 — credential "
                                "likely required")
        elif resp.status_code in (401, 403):
            result["verdict"] = "blocked"
            result["detail"] = f"HTTP {resp.status_code} refused"
        elif resp.status_code == 404:
            result["verdict"] = "moved"
            result["detail"] = "endpoint returned 404 — URL needs updating"
        else:
            result["verdict"] = "error"
            result["detail"] = f"HTTP {resp.status_code}"
    except Exception as exc:                          # noqa: BLE001
        result["seconds"] = round(time.perf_counter() - t0, 2)
        result["verdict"] = "unreachable"
        result["detail"] = f"{type(exc).__name__}: {exc}"[:160]
    return result


def run_probe() -> list[dict]:
    """Probe every source and report agreement with the declared status."""
    results = []
    with traced_layer("L0", "probe source reachability"):
        for src in SOURCES:
            with step(f"probe:{src.key}"):
                r = probe_one(src)
                results.append(r)
                agrees = r["verdict"] == r["declared"] or (
                    r["declared"] == "manual" and r["verdict"] == "manual")
                msg = (f"{src.key:16} {r['verdict']:12} "
                       f"declared={r['declared']:10} "
                       f"{r.get('detail') or ''}")
                (_log.info if agrees else _log.warning)(msg)

    drift = [r for r in results
             if r["verdict"] != r["declared"] and r["declared"] != "manual"]
    if drift:
        _log.warning("%d source(s) disagree with the registry — update "
                     "sources.py and docs/data/", len(drift))
    return results


def main() -> int:
    """CLI entry point: probe every registered source and write the report.

    Always returns 0. A probe is diagnostic — an unreachable host is what
    it is there to report, not a reason to fail the build.
    """
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(paths.METRICS / "source_probe.json"))
    args = ap.parse_args()

    paths.ensure_dirs()
    init_run()
    configure()

    results = run_probe()

    from ..common.log_json import write_json  # local import: small helper
    write_json(args.out, {"probed_on": date.today().isoformat(),
                          "results": results})

    open_n = sum(1 for r in results if r["verdict"] == "open")
    print(f"\n  {open_n}/{len(results)} sources acquirable without "
          f"credentials or manual placement")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
