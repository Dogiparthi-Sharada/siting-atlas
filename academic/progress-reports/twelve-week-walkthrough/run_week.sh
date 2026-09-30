#!/usr/bin/env bash
#
# run_week.sh -- run one week of the walkthrough against the siting-atlas
# repository, then print that week's summary.
#
#   bash run_week.sh 07          run week 7
#   bash run_week.sh 07 --dry    show what it WOULD run, run nothing
#   bash run_week.sh --list      the twelve weeks and their modes
#
# RECOMPUTE weeks invoke the repository's own make targets or modules and
# genuinely re-derive their result, offline, with no API keys. INSPECT weeks
# read a shipped artefact and compute nothing -- those stages need the raw
# source cache, three API keys, ~4 GB of downloads or ninety minutes.
#
# Nothing here writes to the repository except the artefacts a RECOMPUTE
# week legitimately rebuilds. The walkthrough's own pages live beside this
# script, so revising the narrative never touches the code it describes.
#
# SITING_ATLAS=/path/to/clone overrides repository discovery.
#
# EXIT CODES  0 ok · 2 bad usage · 3 repository not found · 4 stage failed

set -uo pipefail
CALLER_PWD="$PWD"; trap 'cd "$CALLER_PWD" 2>/dev/null || true' EXIT

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${SITING_ATLAS:-$(cd "$HERE/../../.." && pwd)/siting-atlas}"

[ -d "$REPO" ] || { echo "siting-atlas not found at: $REPO" >&2
                    echo "set SITING_ATLAS=/path/to/clone" >&2; exit 3; }

# The repository's own venv if it has one, else whatever python is on PATH.
PY="$REPO/.venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3 || true)"
[ -n "$PY" ] || { echo "no python found" >&2; exit 3; }

# Put the venv's bin FIRST on PATH, which is what activating it would do.
# Overriding make's PY is not enough on its own: the repository's `test`
# target shells out to a bare `pytest`, a console script that lives in the
# venv's bin and is invisible to a non-activated shell. Week 12 died with
# "make: pytest: No such file or directory" until this line existed, and
# any future target calling ruff, mkdocs or similar would have died too.
VENV_BIN="$(dirname "$PY")"
case ":$PATH:" in *":$VENV_BIN:"*) ;; *) PATH="$VENV_BIN:$PATH" ;; esac
export PATH

# What each week actually executes inside the repository. Empty = INSPECT,
# so the week prints its summary and touches nothing.
#
# MAKE and PYMOD are placeholders substituted below. The repository's
# Makefile declares `PY ?= python`, which resolves to the SYSTEM python
# unless a venv is active -- and this script is usually run without one, so
# a bare `make cost` died with ModuleNotFoundError. Overriding PY on the
# make command line is the fix; it beats both the default and the
# environment, so the stage runs against the same interpreter the summary
# is read with.
stage_for() {
  case "$1" in
     6) echo "MAKE model"   ;;
     7) echo "MAKE metro"   ;;
     9) echo "MAKE cost"    ;;
    10) echo "PYMOD siting_atlas.cost.station_runner" ;;
    12) echo "MAKE test && MAKE reproduce" ;;
     *) echo "" ;;
  esac
}

if [ "${1:-}" = "--list" ]; then
  "$PY" "$HERE/lib/build_weeks.py" build >/dev/null 2>&1
  sed -n '/^| Week/,/^$/p' "$HERE/README.md"
  exit 0
fi

N="${1:-}"
case "$N" in
  ''|*[!0-9]*) sed -n '3,18p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
N=$((10#$N))
[ "$N" -ge 1 ] && [ "$N" -le 12 ] || { echo "week must be 1-12" >&2; exit 2; }

STAGE="$(stage_for "$N")"
DRY=0; [ "${2:-}" = "--dry" ] && DRY=1

printf '\n  ===== week %02d =====\n' "$N"
if [ -z "$STAGE" ]; then
  printf '  INSPECT: reads a shipped artefact, recomputes nothing\n'
else
  CMD="${STAGE//PYMOD/$PY -m}"
  CMD="${CMD//MAKE/make PY=\"$PY\"}"
  printf '  RECOMPUTE in %s\n    %s\n' "$REPO" "$CMD"
  if [ "$DRY" -eq 1 ]; then
    printf '  --dry: not run\n'
  else
    ( cd "$REPO" && eval "$CMD" ) || { echo "  stage failed" >&2; exit 4; }
  fi
fi

"$PY" "$HERE/lib/build_weeks.py" show "$N"
printf '  page: weeks/WEEK-%02d.md\n\n' "$N"
