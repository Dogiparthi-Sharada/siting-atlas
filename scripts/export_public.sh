#!/usr/bin/env bash
#
# export_public.sh -- build a folder containing EXACTLY what may be published,
#                     and nothing else.
#
# WHAT IT DOES
#   Resolves .gitignore properly, copies the resulting file list into a clean
#   directory beside the repository, then re-checks that directory
#   independently for the things that must never be public. The two passes are
#   deliberate: the first trusts .gitignore, the second does not.
#
#   This exists because .gitignore protects `git add` and NOTHING ELSE. Anyone
#   uploading the working folder through github.com's web page, or zipping it
#   to send somewhere, ships .env, a USD 25 licensed dataset and 12 MB of
#   third-party copyright. The export folder is safe however it is moved.
#
# WHAT IT NEEDS
#   bash, git, and the POSIX toolchain. No Python, no network.
#
# WHAT IT PRODUCES
#   ../siting-atlas-public/ -- overwritten on every run, so it is idempotent.
#   Nothing inside the repository is modified, moved or deleted.
#
# EXIT CODES
#   0  export built and every safety check passed; safe to upload
#   1  a safety check FAILED -- the export was built but MUST NOT be uploaded
#   2  bad usage -- unknown option or stray argument
#   3  cannot locate the repository root from this script's own location
#   4  a prerequisite is missing (git, or this is not a git working tree)
#
# EXAMPLE
#   bash scripts/export_public.sh                 # from anywhere
#   bash scripts/export_public.sh --dry-run       # list, copy nothing
#   DEST=/tmp/out bash scripts/export_public.sh   # somewhere else
#
# ---------------------------------------------------------------------------

set -uo pipefail

# Refuse to be sourced. An EXIT trap in a sourced script fires when the SHELL
# dies, not when the script ends, so the cwd restore below would never run and
# the caller would be left in the repo root.
if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
    echo "export_public.sh must be run, not sourced: bash ${BASH_SOURCE[0]}" >&2
    return 2 2>/dev/null || exit 2
fi

CALLER_PWD="$PWD"
trap 'cd "$CALLER_PWD" 2>/dev/null || true' EXIT

if [ -t 2 ]; then
    C_RED=$'\033[31m'; C_GRN=$'\033[32m'; C_DIM=$'\033[2m'; C_OFF=$'\033[0m'
else
    C_RED=''; C_GRN=''; C_DIM=''; C_OFF=''
fi

FAILED=0
_say()  { printf '%s %s%-4s%s %s\n' "$(date '+%H:%M:%S')" "$2" "$1" "$C_OFF" "${*:3}" >&2; }
info()  { _say INFO "$C_DIM" "$@"; }
ok()    { _say OK   "$C_GRN" "$@"; }
fail()  { _say FAIL "$C_RED" "$@"; FAILED=1; }
die()   { local c="$1"; shift; _say FAIL "$C_RED" "$@"; exit "$c"; }
section() { printf '\n%s== %s%s\n' "$C_DIM" "$*" "$C_OFF" >&2; }

usage() {
    cat <<'EOF'
Usage: export_public.sh [-h] [-v] [-n]

Build a folder containing exactly the publishable files. Read-only w.r.t. the
repository; the destination is overwritten.

  -h, --help     print this and exit 0
  -v, --verbose  trace every command
  -n, --dry-run  list what would be copied, copy nothing

Exit: 0 safe to upload | 1 a safety check failed | 2 bad usage
      3 repo root not found | 4 missing prerequisite

Environment:
  DEST   destination directory (default: ../siting-atlas-public)
EOF
}

VERBOSE=0; DRY=0
while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help)    usage; exit 0 ;;
        -v|--verbose) VERBOSE=1 ;;
        -n|--dry-run) DRY=1 ;;
        --)           shift; break ;;
        *)            usage >&2; die 2 "unexpected argument: $1" ;;
    esac
    shift
done
[ "$VERBOSE" -eq 1 ] && set -x

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"
[ -n "$ROOT" ] && [ -d "$ROOT/src/siting_atlas" ] \
    || die 3 "cannot find the repo root -- expected src/siting_atlas one level up"
cd "$ROOT" || die 3 "cannot cd into $ROOT"
command -v git >/dev/null 2>&1 || die 4 "git is not on PATH"
git rev-parse --git-dir >/dev/null 2>&1 \
    || die 4 "$ROOT is not a git working tree -- .gitignore cannot be resolved without one"

DEST="${DEST:-$ROOT/../siting-atlas-public}"

# ------------------------------------------------------------ the file list
section "resolving .gitignore"
# Tracked files PLUS untracked-but-not-ignored. The second half matters: most
# of this repository has never been committed, and `git ls-files` alone would
# miss it. Files in the index but deleted from disk are skipped below.
LIST="$(mktemp)"; trap 'rm -f "$LIST"; cd "$CALLER_PWD" 2>/dev/null || true' EXIT
{ git ls-files; git ls-files --others --exclude-standard; } | sort -u > "$LIST"
info "$(wc -l < "$LIST") paths before pruning deleted entries"

if [ "$DRY" -eq 1 ]; then
    while IFS= read -r p; do [ -f "$p" ] && echo "$p"; done < "$LIST"
    ok "dry run -- nothing copied"
    exit 0
fi

# ------------------------------------------------------------------- copy
section "copying to $DEST"
rm -rf "$DEST" || die 1 "cannot clear $DEST"
mkdir -p "$DEST" || die 1 "cannot create $DEST"
n=0
while IFS= read -r p; do
    [ -f "$p" ] || continue          # in the index but deleted from disk
    mkdir -p "$DEST/$(dirname "$p")"
    cp -p "$p" "$DEST/$p" && n=$((n + 1))
done < "$LIST"
[ -f .gitignore ] && cp -p .gitignore "$DEST/.gitignore"
ok "$n files copied"

# ------------------------------------------- independent re-check, pass two
# Deliberately does NOT consult .gitignore. If the ignore rules are wrong, the
# first pass is wrong in the same way, and a check that shares an assumption
# with the thing it is checking is not a check.
section "safety re-check (does not trust .gitignore)"

for pat in ".env" ".venv" "subsidy_tracker" "mwpvl_2025q1" \
           "Distribution Network Strategy" ".coverage" "vnc_logs" "id_rsa" "*.pem"; do
    hits="$(find "$DEST" -name "*${pat}*" -not -name ".env.example" 2>/dev/null)"
    if [ -n "$hits" ]; then
        fail "must not ship: $pat"
        printf '              %s\n' $hits >&2
    else
        ok "absent: $pat"
    fi
done

if [ -f "$ROOT/.env" ]; then
    leaked=0
    while IFS='=' read -r k v; do
        case "$k" in ''|\#*) continue ;; esac
        v="${v%\"}"; v="${v#\"}"; v="${v%\'}"; v="${v#\'}"
        [ ${#v} -ge 12 ] || continue
        if grep -rIq -- "$v" "$DEST" 2>/dev/null; then
            fail "the value of \$$k appears inside the export"; leaked=1
        fi
    done < "$ROOT/.env"
    [ $leaked -eq 0 ] && ok "no .env value appears anywhere in the export"
fi

big="$(find "$DEST" -type f -size +25M 2>/dev/null)"
if [ -n "$big" ]; then
    fail "over GitHub's 25 MB web-upload limit:"; printf '              %s\n' $big >&2
else
    ok "every file is under the 25 MB web-upload limit"
fi

huge="$(find "$DEST" -type f -size +100M 2>/dev/null)"
[ -n "$huge" ] && fail "over GitHub's 100 MB hard limit: $huge" \
               || ok "every file is under the 100 MB hard limit"

section "result"
info "$DEST"
info "$(find "$DEST" -type f | wc -l) files, $(du -sh "$DEST" 2>/dev/null | cut -f1)"
if [ $FAILED -eq 0 ]; then
    printf '%sSAFE TO UPLOAD%s -- see PUBLISHING.md\n\n' "$C_GRN" "$C_OFF" >&2
else
    printf '%sDO NOT UPLOAD%s -- clear the FAIL lines above first\n\n' "$C_RED" "$C_OFF" >&2
fi
exit $FAILED
