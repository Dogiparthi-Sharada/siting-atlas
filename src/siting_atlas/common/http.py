"""HTTP with retries, a content-addressed cache, and full request logging.

Every fetch is recorded in ``logs/run-*/http.jsonl`` with URL, status, bytes,
elapsed time and whether it was served from cache. Downloads are written once
into ``data/raw/<source>/<sha256>.<ext>`` and registered in the manifest, so:

  * a re-run costs no network and works offline;
  * a reviewer can re-download from the manifest URLs and verify the hashes.

API keys are read from the environment and are never logged.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode, urlparse

import requests

from . import context, paths
from .logging_setup import get_logger, sink

_log = get_logger("http")
_http_log = sink("http.jsonl")

USER_AGENT = ("SitingAtlas/0.1 (academic research; "
              "https://github.com/siting-atlas)")
TIMEOUT = 60
RETRIES = 3
BACKOFF = 2.0
CHUNK = 1 << 16
_SECRET_PARAMS = {"key", "api_key", "token", "apikey"}

#: Environment variables whose literal values must never be logged.
#: Scrubbed by value as well as by name, so a key that reaches a log
#: without a `key=` prefix is still caught.
_SECRET_ENV_VARS = ("CENSUS_API_KEY", "EIA_API_KEY", "BLS_API_KEY")


@dataclass
class Fetched:
    """Where a download landed and how it got there."""
    path: Path
    url: str
    sha256: str
    bytes: int
    from_cache: bool
    status: int = 200
    headers: dict = field(default_factory=dict)


def _redact(url: str) -> str:
    """Strip credentials from a URL before it reaches any log."""
    parts = urlparse(url)
    if not parts.query:
        return url
    kept = []
    for pair in parts.query.split("&"):
        k, _, _v = pair.partition("=")
        kept.append(f"{k}=<redacted>" if k.lower() in _SECRET_PARAMS else pair)
    return parts._replace(query="&".join(kept)).geturl()


#: `key=<value>` in any text, however the text was built.
_SECRET_RE = re.compile(
    r"\b(" + "|".join(sorted(_SECRET_PARAMS)) + r")=([^&\s'\"<>]+)",
    re.IGNORECASE)

#: `Authorization: Bearer <token>`, which carries no `name=` for the rule
#: above to find. Common in a curl invocation passed to common.shell.run.
_BEARER_RE = re.compile(r"\b(Bearer|Basic)\s+([^\s'\"<>]+)", re.IGNORECASE)


def _scrub(text: object) -> str:
    """Redact credentials from arbitrary text before it reaches a log.

    ``_redact`` only helps for a URL we build ourselves. A credential also
    arrives by routes we do not control: ``requests`` embeds the fully
    expanded URL — query string included — in its exception messages, so
    logging an exception verbatim writes the live key into console.log,
    events.jsonl and errors.log at once. That happened, with a real
    EIA_API_KEY, before this function existed.

    Three passes, because each alone leaks:

    1. Pattern: any ``key=value`` pair whose name looks secret.
    2. Scheme: an ``Authorization: Bearer`` / ``Basic`` credential, which has
       no ``name=`` for pass 1 to key off. Reached via common.shell, where a
       token arrives in argv rather than in a URL.
    3. Literal: the actual values of the credential environment variables, so
       a bare key pasted into a message with no ``name=`` around it is still
       caught.

    All three are idempotent — the replacement text contains ``<`` and ``>``,
    which every pattern excludes — so scrubbing twice is harmless.
    """
    out = _SECRET_RE.sub(r"\1=<redacted>", str(text))
    out = _BEARER_RE.sub(r"\1 <redacted>", out)
    for var in _SECRET_ENV_VARS:
        val = os.environ.get(var)
        # Guard the length: a one-character value would blank out the message.
        if val and len(val) >= 8:
            out = out.replace(val, f"<{var}>")
    return out


def _scrub_cached(target: Path, params: dict, total: int,
                  sha: hashlib._Hash) -> tuple[int, hashlib._Hash]:
    """Remove a credential the server echoed back into its own response.

    The EIA v2 API replies with a ``request.params.api_key`` block containing
    the key just sent. Cached verbatim, that writes a live credential into
    ``data/raw/``. It is gitignored and the committed manifest carries only
    the redacted URL, so nothing was publishable — but the cache is exactly
    what gets copied to a colleague or a cluster.

    Rewriting the file changes its hash, which looks like it breaks the
    "re-download and verify" promise. It does the opposite: the echoed key
    differs per user, so an un-scrubbed EIA response could *never* hash the
    same for two people. Removing it is what makes the artefact reproducible.

    Returns the corrected byte count and hash so the manifest describes the
    file actually on disk.
    """
    sent = {str(v) for k, v in params.items()
            if k.lower() in _SECRET_PARAMS and v and len(str(v)) >= 8}
    if not sent:
        return total, sha
    try:
        blob = target.read_bytes()
    except OSError:
        return total, sha

    cleaned = blob
    for secret in sent:
        cleaned = cleaned.replace(secret.encode(), b"<redacted>")
    if cleaned == blob:
        return total, sha

    target.write_bytes(cleaned)
    _log.debug("scrubbed an echoed credential from %s", paths.rel(target))
    return len(cleaned), hashlib.sha256(cleaned)


def _digest(url: str, params: dict | None) -> str:
    """Cache key: the request identity, not the response."""
    basis = url + ("?" + urlencode(sorted((params or {}).items())) if params
                   else "")
    return hashlib.sha256(basis.encode()).hexdigest()


def _suffix(url: str, default: str = ".bin") -> str:
    """File extension to cache a download under, from its URL path.

    Every suffix is kept so ``.csv.zip`` survives, and the result is
    capped at 12 characters because a query-laden URL can otherwise
    produce an absurd one. Falls back to ``.bin`` when the path has no
    extension at all, which is normal for an API endpoint.
    """
    name = Path(urlparse(url).path).name
    return "".join(Path(name).suffixes)[-12:] or default


def _manifest_append(record: dict) -> None:
    """Append one provenance record to data/raw/manifest.jsonl.

    JSONL and append-only on purpose: the manifest is the artefact a
    reviewer re-downloads from, so a partial write must cost one line
    rather than the whole history.
    """
    paths.RAW.mkdir(parents=True, exist_ok=True)
    with open(paths.MANIFEST, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str) + "\n")


def manifest_entries() -> list[dict]:
    """Every recorded acquisition, for provenance reporting."""
    if not paths.MANIFEST.exists():
        return []
    with open(paths.MANIFEST, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def fetch(url: str, source: str, *, params: dict | None = None,
          headers: dict | None = None, force: bool = False,
          timeout: int = TIMEOUT, expect: str | None = None) -> Fetched:
    """Download ``url`` into the cache for ``source`` and return its location.

    Parameters
    ----------
    source
        Logical dataset name; becomes the cache subdirectory.
    force
        Bypass the cache and re-download.
    expect
        Optional substring the Content-Type must contain. Guards against a
        proxy returning an HTML error page with HTTP 200 — which is exactly
        how the Census API reports a missing key.
    """
    key = _digest(url, params)
    out_dir = paths.RAW / source
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{key[:16]}{_suffix(url)}"
    shown = _redact(url)

    if target.exists() and not force:
        blob = target.read_bytes()
        digest = hashlib.sha256(blob).hexdigest()
        _http_log.debug("http", extra={"fields": {
            "event": "http", "cached": True, "url": shown, "source": source,
            "path": str(target), "bytes": len(blob), "sha256": digest,
            **context.snapshot()}})
        _log.debug("cache hit %s (%d bytes)", paths.rel(target), len(blob))
        return Fetched(target, url, digest, len(blob), True)

    hdrs = {"User-Agent": USER_AGENT, **(headers or {})}
    last: Exception | None = None

    for attempt in range(1, RETRIES + 1):
        t0 = time.perf_counter()
        try:
            with requests.get(url, params=params, headers=hdrs,
                              timeout=timeout, stream=True) as resp:
                status = resp.status_code
                ctype = resp.headers.get("Content-Type", "")
                resp.raise_for_status()
                if expect and expect not in ctype:
                    raise ValueError(
                        f"expected Content-Type containing {expect!r}, "
                        f"got {ctype!r} — the endpoint likely returned an "
                        f"error page with a 200 status")
                tmp = target.with_suffix(target.suffix + ".part")
                sha = hashlib.sha256()
                total = 0
                with open(tmp, "wb") as fh:
                    for chunk in resp.iter_content(CHUNK):
                        if chunk:
                            fh.write(chunk)
                            sha.update(chunk)
                            total += len(chunk)
                tmp.replace(target)        # atomic: no half-written cache
                if params:
                    total, sha = _scrub_cached(target, params, total, sha)
                dt = time.perf_counter() - t0
                digest = sha.hexdigest()

                record = {
                    "event": "http", "cached": False, "url": shown,
                    "source": source, "status": status, "bytes": total,
                    "sha256": digest, "seconds": round(dt, 3),
                    "content_type": ctype, "path": str(target),
                    "attempt": attempt, **context.snapshot()}
                _http_log.debug("http", extra={"fields": record})
                _manifest_append({
                    "fetched_at": datetime.now(UTC).isoformat(
                        timespec="seconds"),
                    "source": source, "url": shown, "sha256": digest,
                    "bytes": total, "content_type": ctype,
                    "path": paths.rel(target), "run_id": context.run_id()})
                _log.info("downloaded %s (%.1f KB in %.1fs)",
                          paths.rel(target), total / 1024, dt)
                return Fetched(target, url, digest, total, False, status,
                               dict(resp.headers))

        except Exception as exc:                      # noqa: BLE001
            last = exc
            dt = time.perf_counter() - t0
            _http_log.debug("http", extra={"fields": {
                "event": "http", "cached": False, "url": shown,
                "source": source,
                "error": _scrub(f"{type(exc).__name__}: {exc}"),
                "attempt": attempt, "seconds": round(dt, 3),
                **context.snapshot()}})
            if attempt < RETRIES:
                wait = BACKOFF ** attempt
                _log.warning("attempt %d/%d failed (%s); retry in %.0fs",
                             attempt, RETRIES, _scrub(exc), wait)
                time.sleep(wait)

    _log.error("giving up on %s: %s", shown, _scrub(last))
    # The message is scrubbed too: an uncaught RuntimeError is printed as a
    # traceback, which lands in errors.log and very often in a CI transcript.
    raise RuntimeError(f"failed to fetch {shown}: {_scrub(last)}") from last


def api_key(env_var: str) -> str | None:
    """Read a key from the environment, logging only whether it was present."""
    val = os.environ.get(env_var)
    _log.debug("api key %s: %s", env_var, "present" if val else "absent")
    return val or None
