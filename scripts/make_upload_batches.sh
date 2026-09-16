#!/usr/bin/env bash
#
# make_upload_batches.sh -- split the publishable export into chunks small
#                           enough for GitHub's web uploader.
#
# WHAT IT DOES
#   Runs scripts/export_public.sh first (so the batches can never be built
#   from a stale export), then copies that export into numbered batch folders
#   of at most 100 files each -- GitHub's per-upload limit on the web.
#
#   Each batch preserves the TOP-LEVEL folder name, because GitHub keeps only
#   the name of the folder you drag, not its path. Dragging `docs/research`
#   creates `research/` at the repository root; dragging a batch containing
#   `docs/research` creates `docs/research/`. Where one top-level folder is
#   too big to fit in a batch, it appears in two batches under the same name
#   and GitHub merges them -- which is why the batches must be uploaded in
#   numeric order.
#
# WHAT IT NEEDS
#   bash, git, the POSIX toolchain, and scripts/export_public.sh beside it.
#
# WHAT IT PRODUCES
#   ../upload-batches/NN-name/ -- wiped and rebuilt on every run, so it is
#   idempotent. Nothing inside the repository is modified.
#
# EXIT CODES
#   0  batches built and every one is within GitHub's limits
#   1  the export failed its safety checks, or a batch exceeds a limit
#   2  bad usage
#   3  cannot locate the repository root
#
# EXAMPLE
#   bash scripts/make_upload_batches.sh
#   DEST=/tmp/batches bash scripts/make_upload_batches.sh
#
# Upload instructions live in ../UPLOAD_STEPS.md. The short version: open a
# batch folder, select everything INSIDE it, drag that in. Never drag the
# batch folder itself -- its name would become a directory in your repository.

set -uo pipefail

if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
    echo "Run, do not source: bash ${BASH_SOURCE[0]}" >&2
    return 2 2>/dev/null || exit 2
fi

CALLER_PWD="$PWD"
trap 'cd "$CALLER_PWD" 2>/dev/null || true' EXIT

if [ -t 2 ]; then C_RED=$'\033[31m'; C_GRN=$'\033[32m'; C_DIM=$'\033[2m'; C_OFF=$'\033[0m'
else C_RED=''; C_GRN=''; C_DIM=''; C_OFF=''; fi
_say(){ printf '%s %s%-4s%s %s\n' "$(date '+%H:%M:%S')" "$2" "$1" "$C_OFF" "${*:3}" >&2; }
info(){ _say INFO "$C_DIM" "$@"; }
ok(){   _say OK   "$C_GRN" "$@"; }
die(){  local c="$1"; shift; _say FAIL "$C_RED" "$@"; exit "$c"; }

case "${1:-}" in
    -h|--help) sed -n '3,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    "") ;;
    *) die 2 "unexpected argument: $1" ;;
esac

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"
[ -n "$ROOT" ] && [ -d "$ROOT/src/siting_atlas" ] || die 3 "cannot find the repo root"
cd "$ROOT" || die 3 "cannot cd into $ROOT"

SRC="$ROOT/../siting-atlas-public"
DEST="${DEST:-$ROOT/../upload-batches}"
LIMIT=100

# Always rebuild the export first. Batches built from a stale export are worse
# than no batches: they look complete and are not. This happened once already.
info "rebuilding the export so the batches cannot be stale"
bash "$ROOT/scripts/export_public.sh" >/dev/null 2>&1 \
    || die 1 "export_public.sh failed its safety checks -- run it directly and read the report"
[ -d "$SRC" ] || die 1 "export not found at $SRC"

rm -rf "$DEST" || die 1 "cannot clear $DEST"
mkdir -p "$DEST"

# copy <batch> <path-relative-to-export>
copy() {
    local b="$1" p="$2"
    [ -e "$SRC/$p" ] || return 0
    mkdir -p "$DEST/$b/$(dirname "$p")"
    cp -rp "$SRC/$p" "$DEST/$b/$p"
}

info "building batches (limit ${LIMIT} files each)"

# 1 -- root files and the four small trees. -a picks up the dotfiles, which is
# where .github and .gitignore live and where a manual selection loses them.
mkdir -p "$DEST/01-root-and-small"
find "$SRC" -maxdepth 1 -type f -exec cp -p {} "$DEST/01-root-and-small/" \;
for d in paper scripts reproducibility tools .github; do copy 01-root-and-small "$d"; done

# 2,3 -- docs is over the limit, so it is split under one name and merged
for d in adr data engineering figures; do copy 02-docs-part1 "docs/$d"; done
mkdir -p "$DEST/02-docs-part1/docs"
find "$SRC/docs" -maxdepth 1 -type f -exec cp -p {} "$DEST/02-docs-part1/docs/" \;
copy 03-docs-part2 "docs/research"

# 4,5 -- src, same treatment
for d in analysis app common cost ingest; do copy 04-src-part1 "src/siting_atlas/$d"; done
mkdir -p "$DEST/04-src-part1/src/siting_atlas"
find "$SRC/src" -maxdepth 1 -type f -exec cp -p {} "$DEST/04-src-part1/src/" \; 2>/dev/null
find "$SRC/src/siting_atlas" -maxdepth 1 -type f \
     -exec cp -p {} "$DEST/04-src-part1/src/siting_atlas/" \;
for d in models report viz warehouse; do copy 05-src-part2 "src/siting_atlas/$d"; done

# 6..9 -- each already under the limit
copy 06-tests        tests
copy 07-outputs      outputs
copy 08-data         data
copy 09-experiments  experiments

# --------------------------------------------------------------- verify
FAILED=0
printf '\n  %-24s %6s %9s %10s\n' BATCH FILES SIZE LARGEST >&2
for d in "$DEST"/*/ ; do
    n=$(find "$d" -type f | wc -l)
    sz=$(find "$d" -type f -printf '%s\n' | awk '{s+=$1} END{printf "%.1f", s/1048576}')
    lg=$(find "$d" -type f -printf '%s\n' | sort -rn | head -1)
    v=""
    [ "$n" -gt "$LIMIT" ] && { v="OVER $LIMIT FILES"; FAILED=1; }
    [ "${lg:-0}" -gt 26214400 ] && { v="FILE OVER 25MB"; FAILED=1; }
    printf '  %-24s %6s %8sM %9.1fM  %s\n' "$(basename "$d")" "$n" "$sz" \
           "$(echo "${lg:-0}/1048576" | bc -l)" "$v" >&2
done

# Nothing may be dropped. A batch set that silently omits files is the failure
# mode this whole script exists to prevent.
( cd "$SRC"  && find . -type f | sed 's|^\./||' ) | sort > /tmp/.b_want.$$
( cd "$DEST" && find . -type f | sed 's|^\./[^/]*/||' ) | sort > /tmp/.b_have.$$
miss=$(comm -23 /tmp/.b_want.$$ /tmp/.b_have.$$ | wc -l)
extra=$(comm -13 /tmp/.b_want.$$ /tmp/.b_have.$$ | wc -l)
if [ "$miss" -ne 0 ]; then
    _say FAIL "$C_RED" "$miss file(s) in the export are in NO batch:"
    comm -23 /tmp/.b_want.$$ /tmp/.b_have.$$ | head -20 | sed 's/^/              /' >&2
    FAILED=1
else
    ok "every export file appears in exactly one batch ($extra unexpected extras)"
fi
rm -f /tmp/.b_want.$$ /tmp/.b_have.$$

echo >&2
info "$DEST"
if [ $FAILED -eq 0 ]; then
    printf '%sBATCHES READY%s -- upload in numeric order. See ../UPLOAD_STEPS.md\n\n' \
           "$C_GRN" "$C_OFF" >&2
else
    printf '%sBATCHES NOT USABLE%s -- clear the problems above\n\n' "$C_RED" "$C_OFF" >&2
fi
exit $FAILED
