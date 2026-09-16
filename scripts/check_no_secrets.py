#!/usr/bin/env python3
"""Refuse to commit a run log, or any file carrying a live credential.

This exists because it already happened. A real EIA_API_KEY was written into
logs/<run>/console.log, events.jsonl and errors.log at once, because
``requests`` puts the fully expanded URL - query string included - into its
exception messages, and the exception was logged verbatim. ``logs/`` is now
gitignored and ``common.http._scrub`` redacts at the source, but both of
those are one ``git add -f`` or one new log sink away from being bypassed.
This hook is the last gate before the object reaches the index.

Three checks, and each catches something the other two miss:

  1. Path: anything under ``logs/``, plus ``.env`` and ``*.key``. Gitignore
     is advisory - ``git add -f`` overrides it; a hook does not.
  2. Literal: the actual value of every secret-looking variable in ``.env``.
     This is the only check that catches a bare key pasted into a message
     with no ``name=`` around it, which is exactly how the leak looked.
  3. Pattern: ``api_key=<20+ alphanumerics>`` in any text file, for a key
     that belongs to somebody else's account and is not in this ``.env``.

Run it over everything, not just the staged set:

    python scripts/check_no_secrets.py --all
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Paths that must never be committed, whatever they contain.
FORBIDDEN_DIRS = ("logs/",)
FORBIDDEN_NAMES = (".env",)
FORBIDDEN_SUFFIXES = (".key", ".pem")

# Variable names in .env whose VALUE is a credential. Kept in step with
# common.http._SECRET_ENV_VARS - that function scrubs the same values on the
# way into a log, this one stops them on the way into a commit.
SECRET_NAME_RE = re.compile(
    r"(?i)(key|token|secret|password|passwd|credential)")

# `api_key=<value>`, however the text was built. The value must be 20+ bare
# alphanumerics: that matches a real Census (40 hex) or EIA (40 alnum) key
# and does NOT match `${{ secrets.CENSUS_API_KEY }}`, `api_key=<redacted>`,
# or an f-string placeholder like `api_key={FAKE}`.
PATTERN_RE = re.compile(
    r"(?i)\b(api[_-]?key|apikey|access[_-]?token|secret[_-]?key|password)"
    r"\s*[=:]\s*[\"']?([A-Za-z0-9]{20,})")

# A value shorter than this is not a credential, and blanking on it would
# make the hook fire on every file. Mirrors the guard in http._scrub.
MIN_SECRET_LEN = 8

SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".docx", ".pptx",
                 ".xlsx", ".zip", ".parquet", ".duckdb", ".bin", ".so"}


def env_secrets(env_path: Path) -> dict[str, str]:
    """Literal credential values from a dotenv file, keyed by variable."""
    out: dict[str, str] = {}
    if not env_path.exists():
        return out
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        name, value = name.strip(), value.strip().strip("'\"")
        if SECRET_NAME_RE.search(name) and len(value) >= MIN_SECRET_LEN:
            out[name] = value
    return out


def bad_path(rel: str) -> str | None:
    """Why this path may not be committed, or None."""
    if any(rel == d.rstrip("/") or rel.startswith(d)
           for d in FORBIDDEN_DIRS):
        return ("run logs are never committed - they record every URL and "
                "SQL statement a run issued")
    if Path(rel).name in FORBIDDEN_NAMES:
        return "holds live credentials"
    if Path(rel).suffix in FORBIDDEN_SUFFIXES:
        return "looks like a private key"
    return None


def scan(path: Path, secrets: dict[str, str]) -> list[str]:
    """Credential findings in one file. Empty list means clean."""
    if path.suffix in SKIP_SUFFIXES or not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []          # binary or unreadable: the path checks cover it

    found = []
    for name, value in secrets.items():
        if value in text:
            found.append(f"contains the live value of ${name}")
    for match in PATTERN_RE.finditer(text):
        line = text[:match.start()].count("\n") + 1
        found.append(f"line {line}: {match.group(1)}=<{len(match.group(2))} "
                     f"chars> looks like a live credential")
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="*", help="paths (pre-commit supplies "
                                             "the staged set)")
    ap.add_argument("--all", action="store_true",
                    help="scan the whole working tree instead")
    args = ap.parse_args(argv)

    if args.all:
        # logs/, .env and data/ are gitignored, so they can never reach a
        # commit by accident and listing them would bury the finding that
        # matters: a credential in a file somebody DOES intend to commit.
        skip = {".git", ".venv", "node_modules", "__pycache__", "data",
                "logs", ".env", ".pytest_cache", ".ruff_cache", "outputs"}
        targets = [p for p in REPO.rglob("*")
                   if p.is_file() and not (skip & set(p.parts))]
    else:
        targets = [Path(f) for f in args.files]

    secrets = env_secrets(REPO / ".env")
    problems: list[str] = []

    for path in targets:
        try:
            rel = str(path.resolve().relative_to(REPO))
        except ValueError:
            rel = str(path)

        reason = bad_path(rel)
        if reason:
            problems.append(f"  {rel}\n      {reason}")
            continue
        for finding in scan(path, secrets):
            problems.append(f"  {rel}\n      {finding}")

    if problems:
        print("BLOCKED - these must not be committed:\n")
        print("\n".join(problems))
        print("\nIf a finding is a false positive, narrow the pattern in "
              "scripts/check_no_secrets.py rather than skipping the hook.")
        return 1

    if args.all:
        print(f"clean: {len(targets)} files, "
              f"{len(secrets)} live secret(s) checked for by value")
    return 0


if __name__ == "__main__":
    sys.exit(main())
