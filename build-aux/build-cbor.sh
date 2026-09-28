#!/bin/sh
# Release archives need no generator while their exact source bytes match.
set -eu
LC_ALL=C
export LC_ALL
. ./build-aux/make-config.sh
load_dbgen_config

mkdir -p build
work=$(mktemp -d build/cbor-sources.XXXXXXXX)
cleanup()
{
    status=$?
    rm -rf "$work"
    if test "$status" -ne 0; then
        rm -f db/ddccontrol-db.cbor db/ddccontrol-db.snapshot db/ddccontrol-db.sources
    fi
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM

if command -v sha256sum >/dev/null 2>&1; then
    hash_command=sha256sum
elif command -v sha256 >/dev/null 2>&1; then
    hash_command=sha256
elif command -v shasum >/dev/null 2>&1; then
    hash_command=shasum
else
    echo 'A SHA-256 utility (sha256sum, sha256 or shasum) is required.' >&2
    exit 1
fi

source_manifest()
{
    for file in db/options.xml db/monitor/*.xml .ci/ddccontrol-dbgen.rev; do
        case "$hash_command" in
            sha256sum) digest=$(sha256sum < "$file") ;;
            sha256) digest=$(sha256 -q < "$file") ;;
            shasum) digest=$(shasum -a 256 < "$file") ;;
        esac
        printf '%s  %s\n' "${digest%% *}" "$file"
    done
}

source_manifest > "$work/before"
if test -e .git || test ! -f db/ddccontrol-db.cbor || test ! -f db/ddccontrol-db.snapshot ||
    test ! -f db/ddccontrol-db.sources || ! cmp -s "$work/before" db/ddccontrol-db.sources; then
    # Remove old artifacts even if the selected generator cannot start.
    rm -f db/ddccontrol-db.cbor db/ddccontrol-db.snapshot db/ddccontrol-db.sources
    "$ddcdbgen_value" convert db db/ddccontrol-db.cbor --snapshot db/ddccontrol-db.snapshot
    source_manifest > "$work/after"
    if ! cmp -s "$work/before" "$work/after"; then
        echo 'CBOR sources changed during generation; retry the build.' >&2
        exit 1
    fi
    mv "$work/after" db/ddccontrol-db.sources
fi
