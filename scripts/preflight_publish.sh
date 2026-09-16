#!/usr/bin/env bash
#
# preflight_publish.sh -- everything that must be true before this repository
#                         is pushed in public.
#
# WHAT IT DOES
#   Runs seven independent checks over the working tree and the git index:
#   leaked secrets, licensed data that must not ship, reproducibility inputs
#   that must ship, the pre-registration seal, GitHub's file-size limits,
#   absolute home paths, and code health (ruff + every module imports).
#   Nothing is written, moved or deleted. Exit 0 means safe to push.
#
#   Written after a near-miss in which a USD 25 licensed dataset and an 11 MB
#   copyrighted PDF were both one `git add` away from being public.
#
# WHAT IT NEEDS
#   bash, git, and the POSIX toolchain (awk, grep, sed, md5sum, stat, xargs).
#   A Python interpreter: $PY if you set it, else <repo>/.venv/bin/python,
#   else python3 from PATH. Ruff must be importable by that interpreter
#   (`python -m ruff`); if it is not, the code check fails rather than being
#   skipped, because a skipped check is worse than a red one.
#
# WHAT IT PRODUCES
#   Nothing on disk. A report on stderr and an exit code. It is read-only and
#   therefore trivially idempotent -- run it as often as you like.
#
# EXIT CODES
#   0  every check passed; safe to push
#   1  at least one check FAILED (the report says which, and what to do)
#   2  bad usage -- unknown option or stray argument
#   3  cannot locate the repository root from this script's own location
#   4  a prerequisite is missing: no git, or no usable Python interpreter
#
#   ("cannot find repo root" used to exit 2; it is now 3, because 2 is
#   reserved repo-wide for bad usage. See scripts/README.md.)
#
# EXAMPLE
#   bash scripts/preflight_publish.sh            # from anywhere
#   bash scripts/preflight_publish.sh --verbose  # with shell tracing
#   bash scripts/preflight_publish.sh --deep     # scan every file on disk
#   PY=/usr/bin/python3.11 bash scripts/preflight_publish.sh
#
# DOCUMENTED EXCEPTION TO `set -e`
#   This script runs `set -uo pipefail` WITHOUT `-e`, and that is deliberate.
#   The whole point is that every check runs and you see the complete list of
#   what is wrong in one pass. Under `-e` the first failing grep would abort
#   the run, you would fix it, run again, and discover the next one -- turning
#   a thirty-second report into a morning. Failures are collected in FAILED
#   and reported at the end instead.

set -uo pipefail

# ------------------------------------------------------------ do not source
# The EXIT trap below cannot help a SOURCED script: sourcing runs everything
# in your own shell, where an EXIT trap fires when the SHELL dies, not when
# the script ends -- and the final `exit $FAILED` would close your terminal.
# Refusing outright is the only honest answer. Run it with `bash`, which is a
# child process and cannot move your shell at all.
if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
    printf 'Do not source this -- run it:  bash %s\n' "${BASH_SOURCE[0]}" >&2
    printf 'Sourcing would move your shell to the repo root and then exit it.\n' >&2
    return 2 2>/dev/null || exit 2
fi

# ---------------------------------------------------------------- the caller
# Put the caller back where they started, via a trap rather than a `cd` at the
# bottom: a trap fires on success, on failure, and on Ctrl-C. A trailing `cd`
# fires on exactly one of those three.
CALLER_PWD="$PWD"
cleanup() { cd "$CALLER_PWD" 2>/dev/null || true; }
trap cleanup EXIT

# ------------------------------------------------------------------- logging
# Everything diagnostic goes to STDERR with a timestamp: `2>report.txt`
# captures the whole story, progress is visible while the slow checks run, and
# stdout stays free for anything a caller might want to parse.
if [ -t 2 ]; then
    C_RED=$'\033[31m'; C_GRN=$'\033[32m'; C_YEL=$'\033[33m'
    C_DIM=$'\033[2m';  C_OFF=$'\033[0m'
else
    C_RED=''; C_GRN=''; C_YEL=''; C_DIM=''; C_OFF=''
fi

FAILED=0

_say() {  # _say LEVEL COLOUR MESSAGE...
    local lvl="$1" col="$2"; shift 2
    printf '%s %s%-4s%s %s\n' "$(date '+%H:%M:%S')" "$col" "$lvl" "$C_OFF" "$*" >&2
}
info() { _say INFO "$C_DIM" "$@"; }
warn() { _say WARN "$C_YEL" "$@"; }
ok()   { _say OK   "$C_GRN" "$@"; }
# In THIS script `fail` records a failed check and carries on -- see the
# `set -e` exception above. Use `die` for the handful of conditions that make
# carrying on pointless.
fail() { _say FAIL "$C_RED" "$@"; FAILED=1; }
note() { printf '              %s\n' "$*" >&2; }
die()  { local code="$1"; shift; _say FAIL "$C_RED" "$@"; exit "$code"; }
section() { printf '\n%s== %s%s\n' "$C_DIM" "$*" "$C_OFF" >&2; }

# --------------------------------------------------------------------- usage
usage() {
    cat <<'EOF'
Usage: preflight_publish.sh [-h] [-v] [-d]

Check that this repository is safe to push in public. Read-only.

  -h, --help     print this and exit 0
  -v, --verbose  trace every command (set -x)
  -d, --deep     scan every file on disk for secrets, not just the
                 publishable set. Slower. Use before zipping or
                 uploading the working folder, where .gitignore does
                 not apply.

Exit: 0 safe to push | 1 a check failed | 2 bad usage
      3 repo root not found | 4 missing prerequisite (git or python)

Environment:
  PY   Python interpreter to use (default: <repo>/.venv/bin/python, else python3)
EOF
}

VERBOSE=0; DEEP=0
while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help)    usage; exit 0 ;;
        -v|--verbose) VERBOSE=1 ;;
        -d|--deep)    DEEP=1 ;;
        --)           shift; break ;;
        -*)           usage >&2; die 2 "unknown option: $1" ;;
        *)            usage >&2; die 2 "unexpected argument: $1" ;;
    esac
    shift
done
if [ "$VERBOSE" -eq 1 ]; then set -x; fi

# ----------------------------------------------------------------- preflight
# Locate the repo, then prove the tools exist, BEFORE running any check. A
# check that fails because grep is missing is a lie about the repository.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"
if [ -z "$ROOT" ] || [ ! -d "$ROOT/src/siting_atlas" ]; then
    die 3 "cannot find the repo root from ${BASH_SOURCE[0]} -- expected src/siting_atlas one level up"
fi
cd "$ROOT" || die 3 "cannot cd into $ROOT"

for BIN in git awk grep sed md5sum stat xargs find; do
    if ! command -v "$BIN" >/dev/null 2>&1; then
        die 4 "required binary '$BIN' is not on PATH -- install coreutils/git and retry"
    fi
done
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    die 4 "$ROOT is not a git working tree -- the licensing, size and path checks all read the index"
fi

PY="${PY:-$ROOT/.venv/bin/python}"
if [ ! -x "$PY" ]; then PY="$(command -v python3 2>/dev/null || true)"; fi
if [ -z "$PY" ] || ! "$PY" -c '' 2>/dev/null; then
    die 4 "no usable Python interpreter -- set PY=/path/to/python, or create the venv: python3 -m venv .venv"
fi

info "repo   $ROOT"
info "python $PY"

# ----------------------------------------------------------------- secrets
section "secrets"
if [ -f .env ]; then
    # Scan only what could actually be published. Grepping the whole tree took
    # over five minutes here, because data/ is several GB and .venv is tens of
    # thousands of files -- and a check nobody runs because it is slow protects
    # nothing. Publishable = present, not ignored. That is the same set
    # export_public.sh copies and the same set `git add .` would stage.
    #
    # --deep restores the everything-on-disk scan. Use it if you are about to
    # move the working folder somewhere (a zip, a USB stick, a web upload),
    # because then .gitignore stops being relevant and an ignored file travels.
    SCAN_LIST="$(mktemp)"
    if [ "$DEEP" -eq 1 ]; then
        info "deep scan: every file on disk (slow, minutes)"
        find . -type f -not -path "./.git/*" -not -path "./.venv/*" \
             -not -name ".env" -print > "$SCAN_LIST" 2>/dev/null
    else
        info "scanning the publishable set ($(
            { git ls-files; git ls-files --others --exclude-standard; } \
            | sort -u | wc -l) paths); --deep scans everything on disk"
        { git ls-files; git ls-files --others --exclude-standard; } \
            | sort -u | grep -v '^\.env$' > "$SCAN_LIST"
    fi

    leaked=0
    while IFS='=' read -r k v; do
        case "$k" in ''|\#*) continue ;; esac
        v="${v%\"}"; v="${v#\"}"; v="${v%\'}"; v="${v#\'}"
        [ ${#v} -ge 12 ] || continue
        if tr '\n' '\0' < "$SCAN_LIST" \
           | xargs -0 -r grep -lI -- "$v" 2>/dev/null | grep -q .; then
            fail "the value of \$$k from .env appears in a publishable file"
            note "rotate the key, then find the copy and remove it before pushing."
            leaked=1
        fi
    done < .env
    rm -f "$SCAN_LIST"
    if [ $leaked -eq 0 ]; then
        [ "$DEEP" -eq 1 ] \
            && ok "no .env value appears anywhere on disk" \
            || ok "no .env value appears in any publishable file"
    fi
else
    ok "no .env present"
fi

if git log --all --oneline -- .env 2>/dev/null | grep -q .; then
    fail ".env appears in git history"
    note "rotate the keys -- history cannot be unsaid, and a rewrite does not help anyone who already cloned."
else
    ok ".env never committed"
fi

# --------------------------------------------------------------- licensing
section "licensing"
must_ignore="data/external/subsidies
data/raw/mwpvl/mwpvl_2025q1_network_article.pdf
data/raw/mwpvl/Amazon.com Distribution Network Strategy.pdf"
while IFS= read -r f; do
    [ -e "$f" ] || continue
    if git check-ignore -q "$f" 2>/dev/null; then
        ok "excluded: $f"
    else
        fail "WOULD BE PUBLISHED: $f"
        note "purchased or third-party copyright -- must not ship."
        note "remedy: add the path to .gitignore, then re-run this script."
    fi
done <<< "$must_ignore"

# --------------------------------------------------- reproducibility inputs
section "reproducibility"
must_ship="data/processed/panel.parquet
data/interim/cbp_detail.parquet
data/external/facility_panel/national_facilities_expanded.csv
data/interim/mwpvl_facilities.csv"
# Three states, not two, and the distinction matters. This check originally
# reported "ships" for anything present and not ignored -- which is right for a
# fresh `git init` + `git add .`, and right for scripts/export_public.sh, but
# WRONG for a push from the existing index, where an untracked file simply does
# not go. It printed reassuring green for four files including the 693-row
# panel that most results rest on, none of which was tracked. A guard that
# answers a different question from the one you asked is worse than no guard.
untracked_any=0
while IFS= read -r f; do
    if [ ! -e "$f" ]; then
        fail "missing: $f"
        note "rebuild it with the Makefile: make panel (see Makefile for the stage)"
    elif git check-ignore -q "$f" 2>/dev/null; then
        fail "gitignored but required for an offline clone: $f"
        note "remedy: un-ignore it in .gitignore -- a fresh clone cannot run \`make reproduce\` without it."
    elif git ls-files --error-unmatch "$f" >/dev/null 2>&1; then
        ok "tracked: $f"
    else
        warn "not ignored, but NOT YET TRACKED: $f"
        untracked_any=1
    fi
done <<< "$must_ship"

if [ "$untracked_any" -eq 1 ]; then
    note "Those files WILL be included by \`git add .\` on a fresh init, and by"
    note "scripts/export_public.sh. They will NOT be included by a push from the"
    note "current index. Run \`git add\` on them first if you are pushing this repo"
    note "as it stands."
fi

# ------------------------------------------------------------- prereg seal
section "pre-registration seal"
if [ -f docs/PREREG_METRO_MODEL.md ] && [ -f outputs/metrics/metro_entry.json ]; then
    recorded=$("$PY" -c "import json;print(json.load(open('outputs/metrics/metro_entry.json')).get('prereg_md5',''))" 2>/dev/null)
    actual=$(md5sum docs/PREREG_METRO_MODEL.md | cut -d' ' -f1)
    if [ -n "$recorded" ] && [ "$recorded" = "$actual" ]; then
        ok "seal intact ($actual)"
    else
        fail "seal BROKEN in docs/PREREG_METRO_MODEL.md -- recorded $recorded, actual $actual"
        note "restore: cp reproducibility/seals/PREREG_METRO_MODEL.*.md docs/PREREG_METRO_MODEL.md"
    fi
else
    fail "docs/PREREG_METRO_MODEL.md or outputs/metrics/metro_entry.json is missing"
    note "the seal proves the model was specified before it was fitted; without"
    note "both files there is nothing to prove. Regenerate: make metro"
fi

# --------------------------------------------------------------- size limits
section "size"
big=$(git ls-files -z 2>/dev/null | xargs -0 -r stat -c '%s %n' 2>/dev/null \
      | awk '$1 > 100*1024*1024 {print $2}')
if [ -n "$big" ]; then
    fail "tracked file(s) over GitHub's 100 MB hard limit:"
    while IFS= read -r b; do note "$b"; done <<< "$big"
    note "remedy: git rm --cached the file and add it to .gitignore, or use Git LFS."
else
    ok "no tracked file exceeds 100 MB"
fi
total=$(git ls-files -z 2>/dev/null | xargs -0 -r stat -c '%s' 2>/dev/null | awk '{s+=$1} END{printf "%.1f", s/1048576}')
info "tracked payload: ${total:-0} MB"

# ------------------------------------------------------------ absolute paths
section "paths"
hits=$(git ls-files -z 2>/dev/null \
       | xargs -0 -r grep -rIl -- "/weka/emulation01/users" 2>/dev/null \
       | grep -v "^docs/AUDIT_" | head -5)
if [ -n "$hits" ]; then
    fail "absolute home paths in tracked files -- they will not resolve for anyone else:"
    while IFS= read -r h; do note "$h"; done <<< "$hits"
    note "remedy: derive the path from \${BASH_SOURCE[0]} or __file__ instead."
else
    ok "no absolute home paths in tracked files (the dated audit is exempt)"
fi

# --------------------------------------------------------------- code health
section "code"
if "$PY" -m ruff check src tests >/dev/null 2>&1; then
    ok "ruff clean"
else
    fail "ruff reports problems in src/ or tests/"
    note "see them: $PY -m ruff check src tests"
fi

if "$PY" - <<'PYEOF' >/dev/null 2>&1
import importlib, os, sys
bad = []
for d, _, fs in os.walk('src/siting_atlas'):
    if '__pycache__' in d:
        continue
    for f in fs:
        if f.endswith('.py'):
            m = os.path.join(d, f)[4:-3].replace('/', '.').removesuffix('.__init__')
            try:
                importlib.import_module(m)
            except Exception:
                bad.append(m)
sys.exit(1 if bad else 0)
PYEOF
then
    ok "every module under src/ imports"
else
    fail "a module under src/ does not import -- a retirement probably moved its dependency"
    note "find it: $PY -c \"import siting_atlas.<module>\" for the suspects, or run: $PY -m pytest --collect-only -q"
fi

# ---------------------------------------------------------------- the verdict
printf '\n' >&2
if [ $FAILED -eq 0 ]; then
    printf '%sPREFLIGHT PASSED%s - safe to push\n\n' "$C_GRN" "$C_OFF" >&2
else
    printf '%sPREFLIGHT FAILED%s - do not push until the FAIL lines are clear\n\n' "$C_RED" "$C_OFF" >&2
fi
exit $FAILED
