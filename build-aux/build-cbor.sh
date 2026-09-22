#!/bin/sh
# Release archives install the generated artifact without Python. Checkouts
# regenerate each time so deletions and same-mtime edits cannot hide staleness.
set -eu
LC_ALL=C
export LC_ALL
mkdir -p build
inventory=build/cbor-source-files
{
    printf '%s\n' db/options.xml
    for file in db/monitor/*.xml; do printf '%s\n' "$file"; done
} > "$inventory"
rebuild=no
if test -e .git || test ! -f db/ddccontrol-db.cbor || test ! -f db/ddccontrol-db.snapshot ||
    test ! -f db/ddccontrol-db.sources || ! cmp -s "$inventory" db/ddccontrol-db.sources; then
    rebuild=yes
else
    while IFS= read -r file; do
        if test "$file" -nt db/ddccontrol-db.cbor; then rebuild=yes; break; fi
    done < "$inventory"
    for file in scripts/cbor-db.py scripts/cbor/*.py; do
        if test "$file" -nt db/ddccontrol-db.cbor; then rebuild=yes; break; fi
    done
fi
if test "$rebuild" = yes; then
    # Remove old artifacts even if Python is missing or cannot start.
    rm -f db/ddccontrol-db.cbor db/ddccontrol-db.snapshot db/ddccontrol-db.sources
    "${PYTHON:-python3}" scripts/cbor-db.py convert db db/ddccontrol-db.cbor \
        --snapshot db/ddccontrol-db.snapshot
    cp "$inventory" db/ddccontrol-db.sources
fi
