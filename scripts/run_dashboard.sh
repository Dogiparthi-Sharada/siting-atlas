#!/usr/bin/env bash
#
# run_dashboard.sh -- serve the cost-to-serve Streamlit dashboard.
#
# WHAT IT DOES
#   Puts src/ on PYTHONPATH and starts Streamlit on the app. That export is
#   the whole reason this launcher exists: Streamlit execs the app file as a
#   top-level script, so it has no parent package, and the app is written with
#   absolute `siting_atlas.*` imports. Running
#   `streamlit run src/siting_atlas/app/dashboard.py` by hand dies with
#   ModuleNotFoundError: siting_atlas.
#
#   This is what `make app` runs. It BLOCKS -- the server runs in the
#   foreground until you Ctrl-C it.
#
# WHAT IT NEEDS
#   A Python interpreter with streamlit installed (set PYTHON to choose one;
#   default is the repo venv, then python3), and at least one cost table in
#   outputs/tables/cost_to_serve_*.parquet. Both are checked before the server
#   starts, so a person who launches this and tabs away does not discover the
#   failure in a browser five minutes later.
#
# WHAT IT PRODUCES
#   Nothing on disk. A web server on http://localhost:$PORT (default 8501).
#   Idempotent in the sense that it changes nothing; but only one process can
#   hold a port, so a second concurrent run fails in Streamlit with EADDRINUSE
#   -- use PORT= to pick another.
#
# EXIT CODES
#   0  clean shutdown (Streamlit exited 0), or --help / a successful --dry-run
#   1  an unexpected failure
#   2  bad usage -- unknown option, stray argument, or a non-numeric PORT
#   3  streamlit is not installed in the chosen interpreter
#   4  no cost tables in outputs/tables/ -- there is nothing to display
#
#   Note for anyone with old shell history: codes 3 and 4 both used to be 2.
#   They are now distinct so a wrapper can tell "you typed it wrong" from
#   "the data is not built yet".
#
# EXAMPLE
#   bash scripts/run_dashboard.sh                 # http://localhost:8501
#   PORT=8600 bash scripts/run_dashboard.sh       # somewhere else
#   bash scripts/run_dashboard.sh --dry-run       # print the command, start nothing

set -euo pipefail

# ------------------------------------------------------------ do not source
# The last line `exec`s Streamlit, which REPLACES the current process. Run
# with `bash`, that is a child and your shell is untouched. `source` it and
# your interactive shell becomes a Streamlit server, which you cannot get out
# of except by killing it.
if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
    printf 'Do not source this -- run it:  bash %s\n' "${BASH_SOURCE[0]}" >&2
    printf 'It execs Streamlit, which would replace your interactive shell.\n' >&2
    return 2 2>/dev/null || exit 2
fi

# ---------------------------------------------------------------- the caller
# Restored by a trap so the caller's shell is never left in the repo root, on
# any exit path. It cannot fire after the final `exec` -- at that point this
# process no longer exists -- but by then nothing needs restoring, because
# `bash script.sh` ran in a child and the caller's own cwd was never touched.
CALLER_PWD="$PWD"
cleanup() { cd "$CALLER_PWD" 2>/dev/null || true; }
trap cleanup EXIT

# ------------------------------------------------------------------- logging
if [ -t 2 ]; then
    C_RED=$'\033[31m'; C_GRN=$'\033[32m'; C_YEL=$'\033[33m'
    C_DIM=$'\033[2m';  C_OFF=$'\033[0m'
else
    C_RED=''; C_GRN=''; C_YEL=''; C_DIM=''; C_OFF=''
fi
_say() {  # _say LEVEL COLOUR MESSAGE...
    local lvl="$1" col="$2"; shift 2
    printf '%s %s%-4s%s %s\n' "$(date '+%H:%M:%S')" "$col" "$lvl" "$C_OFF" "$*" >&2
}
info() { _say INFO "$C_DIM" "$@"; }
warn() { _say WARN "$C_YEL" "$@"; }
ok()   { _say OK   "$C_GRN" "$@"; }
fail() { _say FAIL "$C_RED" "$@"; }
note() { printf '              %s\n' "$*" >&2; }
die()  { local code="$1"; shift; fail "$@"; exit "$code"; }

# --------------------------------------------------------------------- usage
usage() {
    cat <<'EOF'
Usage: run_dashboard.sh [-h] [-v] [-n]

Serve the cost-to-serve dashboard. Blocks until Ctrl-C.

  -h, --help     print this and exit 0
  -v, --verbose  trace every command (set -x)
  -n, --dry-run  run the checks and print the streamlit command; start nothing

Exit: 0 clean shutdown | 1 unexpected failure | 2 bad usage
      3 streamlit not installed | 4 no cost tables to display

Environment:
  PORT     port to listen on            (default: 8501)
  PYTHON   interpreter to run under     (default: <repo>/.venv/bin/python, else python3)
EOF
}

VERBOSE=0
DRY_RUN=0
while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help)    usage; exit 0 ;;
        -v|--verbose) VERBOSE=1 ;;
        -n|--dry-run) DRY_RUN=1 ;;
        --)           shift; break ;;
        -*)           usage >&2; die 2 "unknown option: $1" ;;
        *)            usage >&2; die 2 "unexpected argument: $1" ;;
    esac
    shift
done
if [ "$VERBOSE" -eq 1 ]; then set -x; fi

# ----------------------------------------------------------------- preflight
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"
if [ -z "$REPO" ] || [ ! -f "$REPO/src/siting_atlas/app/dashboard.py" ]; then
    die 1 "cannot find the repo root from ${BASH_SOURCE[0]} -- expected src/siting_atlas/app/dashboard.py one level up"
fi
cd "$REPO" || die 1 "cannot cd into $REPO"

PORT="${PORT:-8501}"
case "$PORT" in
    ''|*[!0-9]*) die 2 "PORT must be a number, got '$PORT'" ;;
esac

PY="${PYTHON:-$REPO/.venv/bin/python}"
if [ ! -x "$PY" ]; then PY="$(command -v python3 2>/dev/null || true)"; fi
if [ -z "$PY" ] || ! "$PY" -c '' 2>/dev/null; then
    die 3 "no usable Python interpreter -- set PYTHON=/path/to/python, or create the venv: python3 -m venv .venv"
fi

if ! "$PY" -c "import streamlit" 2>/dev/null; then
    fail "streamlit is not installed in $PY"
    note "install it:  $PY -m pip install '.[viz]'"
    note "that needs network access; see the offline note in README.md"
    exit 3
fi

# Checked here as well as inside the app: a person who runs the launcher and
# then tabs away should not have to read the failure in a browser.
if ! compgen -G "outputs/tables/cost_to_serve_*.parquet" >/dev/null; then
    fail "no cost tables in $REPO/outputs/tables/ -- the dashboard would open empty"
    note "generate them:  make cost"
    note "or directly:    PYTHONPATH=src $PY -m siting_atlas.cost.runner --all-scenarios"
    exit 4
fi

NTAB=$(find outputs/tables -name 'cost_to_serve_*.parquet' 2>/dev/null | wc -l)
info "repo   $REPO"
info "python $PY"
info "tables $NTAB cost scenario(s)"

export PYTHONPATH="$REPO/src${PYTHONPATH:+:$PYTHONPATH}"

if [ "$DRY_RUN" -eq 1 ]; then
    warn "dry run -- not starting the server"
    note "would run: PYTHONPATH=$PYTHONPATH $PY -m streamlit run src/siting_atlas/app/dashboard.py --server.port $PORT --server.headless true --browser.gatherUsageStats false"
    exit 0
fi

ok "starting on http://localhost:$PORT  (Ctrl-C to stop)"

# `exec` rather than a plain call: Streamlit becomes this process, so Ctrl-C
# and any `kill` from a supervisor reach it directly instead of stopping a
# wrapper shell and orphaning the server.
exec "$PY" -m streamlit run src/siting_atlas/app/dashboard.py \
    --server.port "$PORT" \
    --server.headless true \
    --browser.gatherUsageStats false
