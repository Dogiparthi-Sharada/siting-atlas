#!/usr/bin/env bash
#
# build.sh -- regenerate all twelve week pages and the index from whatever
# the siting-atlas artefacts currently say.
#
# Safe to run any time. It READS the repository and writes only into this
# directory, so rebuilding the narrative can never disturb the code it
# describes or add anything to an upload batch.
#
# Re-run it after any repository stage rebuilds: the pages quote run_ids and
# build dates, and a stale page is worse than no page because it looks
# current.
#
# SITING_ATLAS=/path/to/clone overrides repository discovery.
#
# EXIT CODES  0 all twelve built · 3 repository not found
#             1 built, but at least one artefact was unreadable

set -uo pipefail
CALLER_PWD="$PWD"; trap 'cd "$CALLER_PWD" 2>/dev/null || true' EXIT

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${SITING_ATLAS:-$(cd "$HERE/../../.." && pwd)/siting-atlas}"
[ -d "$REPO" ] || { echo "siting-atlas not found at: $REPO" >&2; exit 3; }

PY="$REPO/.venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3 || true)"
[ -n "$PY" ] || { echo "no python found" >&2; exit 3; }

"$PY" "$HERE/lib/build_weeks.py" build
