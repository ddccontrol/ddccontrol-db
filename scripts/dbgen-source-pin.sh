#!/bin/sh
# Read data, never shell-source a revision pin from a pull request.
set -eu

fail() {
    printf '%s\n' "dbgen-source-pin: $*" >&2
    exit 1
}

case $# in
    0)
        repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
        revision_file="$repo/.ci/ddccontrol-dbgen.rev"
        toolchain_file="$repo/.ci/ddccontrol-dbgen.toolchain"
        ;;
    2) revision_file=$1; toolchain_file=$2 ;;
    *) fail "usage: $0 [revision-file toolchain-file]" ;;
esac

revision=$(cat "$revision_file")
case "$revision" in
    ''|*[!0-9a-f]*) fail "revision must be a full lowercase Git commit SHA" ;;
esac
[ "${#revision}" -eq 40 ] || fail "revision must contain 40 hexadecimal digits"

toolchain=$(cat "$toolchain_file")
case "$toolchain" in
    ''|*[!0-9.]*) fail "Rust toolchain must be a numeric release, such as 1.85.0" ;;
esac
printf '%s\n' "$toolchain" | LC_ALL=C grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' ||
    fail "Rust toolchain must have three numeric components"

printf 'revision=%s\ntoolchain=%s\n' "$revision" "$toolchain"
