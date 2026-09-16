#!/usr/bin/env bash
#
# build_all.sh -- build every deliverable document and validate it.
#
# WHAT IT DOES
#   Three stages, in an order that matters:
#     1. figures   tools/figures/build_all.py       -> docs/figures/*.png
#     2. proposal  tools/proposal/build_v5.py       -> docs/proposal/*.docx
#     3. decks     tools/deck/build_deck.py         -> docs/proposal/*.pptx
#        then tools/deck/check_layout.py on each deck
#   Figures come first because they are EMBEDDED in both the proposal and the
#   decks: build them last and you ship yesterday's charts inside today's
#   document. The layout check is not optional either -- a slide that overflows
#   its box renders fine locally and clips in PowerPoint.
#
#   This is what `make docs` runs.
#
# WHAT IT NEEDS
#   A Python interpreter with the document toolchain installed (python-docx,
#   python-pptx, matplotlib). Set PYTHON to choose one; the default is the
#   repo venv, then python3 from PATH. The three builder scripts under tools/
#   must exist. All of this is checked before any work starts.
#
# WHAT IT PRODUCES
#   docs/figures/*.png, docs/proposal/*.docx, docs/proposal/*.pptx.
#   Overwritten in place, so the script is idempotent in effect: running it
#   twice leaves the same documents. NOT byte-for-byte idempotent -- .docx and
#   .pptx are zip containers and embed a build timestamp, so `git diff` will
#   show a change even when nothing moved. Do not treat a dirty tree after a
#   rebuild as evidence that content changed.
#
# EXIT CODES
#   0  every document built and every layout check passed
#   1  an unexpected failure (see the traceback above the FAIL line)
#   2  bad usage -- unknown option or stray argument
#   3  a prerequisite is missing: no Python, or a builder script is absent
#   4  a build stage failed (figures, proposal or deck)
#   5  a deck failed its layout check -- it built, but it is not shippable
#
# EXAMPLE
#   bash scripts/build_all.sh                 # from anywhere
#   bash scripts/build_all.sh --dry-run       # list the commands, run nothing
#   PYTHON=/usr/bin/python3.11 bash scripts/build_all.sh --verbose
#
# NOTE ON THE MISSING FOURTH STAGE
#   There used to be a "DOCS (Markdown -> plain ASCII text)" stage that
#   rendered a .txt twin of every Markdown file. The twins were removed from
#   this repository on 2026-09-16: GitHub renders Markdown natively, so they
#   were pure duplication, and five had drifted from their .md source --
#   including two defence documents a reader would have trusted.
#   scripts/build_docs.sh and tools/docs/md_to_txt.py are DELETED rather than
#   left callable, because leaving the generator in place means the next
#   `make docs` silently recreates all 113 of them. Do not add the stage back.

set -euo pipefail

# ------------------------------------------------------------ do not source
# The EXIT trap below cannot help a SOURCED script: sourcing runs everything
# in your own shell, and an EXIT trap there fires when the shell dies, not
# when the script ends -- so `. build_all.sh` would return you to a prompt
# sitting in the repo root. Refusing outright is the only honest answer. Run
# it with `bash`, which is a child process and cannot move your shell at all.
if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
    printf 'Do not source this -- run it:  bash %s\n' "${BASH_SOURCE[0]}" >&2
    printf 'Sourcing would leave your shell in the repo root.\n' >&2
    return 2 2>/dev/null || exit 2
fi

# ---------------------------------------------------------------- the caller
# Restored by a trap, not by a `cd` at the bottom: this script cds into the
# repo root and `set -e` can abort it at any line. A trap is the only form
# that also fires on failure and on Ctrl-C.
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
stage() { printf '\n%s---- %s ----%s\n' "$C_DIM" "$*" "$C_OFF" >&2; }

# --------------------------------------------------------------------- usage
usage() {
    cat <<'EOF'
Usage: build_all.sh [-h] [-v] [-n]

Build and validate every deliverable document: figures, then the proposal,
then the decks (each layout-checked).

  -h, --help     print this and exit 0
  -v, --verbose  trace every command (set -x)
  -n, --dry-run  print the commands that would run; touch nothing

Exit: 0 all built and valid | 1 unexpected failure | 2 bad usage
      3 missing prerequisite | 4 a build stage failed | 5 a layout check failed

Environment:
  PYTHON   interpreter to build with (default: <repo>/.venv/bin/python, else python3)
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

# `run` is what makes --dry-run honest: every command with a side effect goes
# through it, so there is no second code path that can drift from the real one.
run() {
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '              %swould run:%s %s\n' "$C_YEL" "$C_OFF" "$*" >&2
        return 0
    fi
    "$@"
}

# ----------------------------------------------------------------- preflight
# Everything is checked before the first builder runs. A missing python-pptx
# discovered at stage 3 has already cost you the figures and the proposal --
# and worse, leaves the tree half-rebuilt.
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"
if [ -z "$REPO" ] || [ ! -d "$REPO/tools" ]; then
    die 3 "cannot find the repo root from ${BASH_SOURCE[0]} -- expected tools/ one level up"
fi
cd "$REPO" || die 3 "cannot cd into $REPO"

PY="${PYTHON:-$REPO/.venv/bin/python}"
if [ ! -x "$PY" ]; then PY="$(command -v python3 2>/dev/null || true)"; fi
if [ -z "$PY" ] || ! "$PY" -c '' 2>/dev/null; then
    die 3 "no usable Python interpreter -- set PYTHON=/path/to/python, or create the venv: python3 -m venv .venv"
fi

BUILDERS="tools/figures/build_all.py
tools/proposal/build_v5.py
tools/deck/build_deck.py
tools/deck/check_layout.py"
while IFS= read -r B; do
    if [ ! -f "$B" ]; then
        die 3 "builder script is missing: $REPO/$B -- this script cannot build the documents without it (restore it from git: git checkout -- $B)"
    fi
done <<< "$BUILDERS"

# docx/pptx/PIL come from the `docs` extra; matplotlib is a core dependency
# because `make figures` is a pipeline stage. Different remedies, so they are
# reported separately rather than as one vague "install the deps".
for MOD in docx pptx PIL; do
    if ! "$PY" -c "import $MOD" 2>/dev/null; then
        die 3 "Python module '$MOD' is not importable by $PY -- install the document toolchain: $PY -m pip install '.[docs]'"
    fi
done
if ! "$PY" -c "import matplotlib" 2>/dev/null; then
    die 3 "matplotlib is not importable by $PY -- it is a core dependency: $PY -m pip install -e ."
fi

info "repo   $REPO"
info "python $PY"
if [ "$DRY_RUN" -eq 1 ]; then warn "dry run -- nothing will be written"; fi

# ------------------------------------------------------------- 1/3  figures
stage "1/3  FIGURES  (auto-fit labels, edge-anchored connectors)"
if ! run "$PY" tools/figures/build_all.py; then
    die 4 "tools/figures/build_all.py failed -- the proposal and both decks embed these figures, so nothing downstream was built"
fi
ok "figures built"

# ------------------------------------------------------------ 2/3  proposal
# v5 is the current deliverable and is rendered from docs/proposal/PROPOSAL_V5.md,
# so the .md and the .docx cannot drift apart. This line used to run
# build_v4.py, which regenerated the SUPERSEDED v4 document and never touched
# v5 -- see docs/AUDIT_2026_09_14.md section 2.7. v4 is historical
# (docs/proposal/README.md) and is deliberately no longer rebuilt; to reproduce
# it, run tools/proposal/build_v4.py by hand.
stage "2/3  PROPOSAL  (Word, figures embedded)"
if ! run "$PY" tools/proposal/build_v5.py; then
    die 4 "tools/proposal/build_v5.py failed -- check docs/proposal/PROPOSAL_V5.md renders, and that the figures from stage 1 exist"
fi
ok "proposal built"

# --------------------------------------------------------------- 3/3  decks
stage "3/3  DECKS  (PowerPoint 16:9, presenter notes)"
if ! run "$PY" tools/deck/build_deck.py; then
    die 4 "tools/deck/build_deck.py failed -- no deck was produced"
fi
for V in v1_overview v2_technical; do
    DECK="docs/proposal/Siting_Atlas_Deck_${V}.pptx"
    info "validating $V"
    if ! run "$PY" tools/deck/check_layout.py "$DECK"; then
        die 5 "$DECK failed its layout check -- a box overflows or a slide violates the template. The deck EXISTS but must not be sent; fix tools/deck/build_deck.py and rebuild."
    fi
done
ok "decks built and validated"

# ------------------------------------------------------------------ artifacts
stage "artifacts"
if [ "$DRY_RUN" -eq 1 ]; then
    warn "dry run -- no artifacts to list"
    exit 0
fi
ls -1sh docs/proposal/*.docx docs/proposal/*.pptx 2>/dev/null | while IFS= read -r L; do
    note "$L"
done
NFIG=$(find docs/figures -name '*.png' 2>/dev/null | wc -l)
note "$NFIG figures"
ok "build complete"
