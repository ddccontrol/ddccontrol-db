#!/bin/sh
# Integration checks use immutable expected files and run no monitor commands.
set -eu

repo=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd)
fixtures="$repo/tests/cbor/fixtures"
requested_generator=${DDCDBGEN:-ddccontrol-dbgen}
generator=$(command -v "$requested_generator") || {
    printf '%s\n' "DDCDBGEN executable not found: $requested_generator" >&2
    exit 1
}
case "$generator" in
    /*) ;;
    *) generator="$(CDPATH='' cd -- "$(dirname -- "$generator")" && pwd)/$(basename -- "$generator")" ;;
esac

work=$(mktemp -d "${TMPDIR:-/tmp}/ddccontrol-dbgen-test.XXXXXXXX")
trap 'rm -rf "$work"' EXIT HUP INT TERM

expect_failure() {
    if "$@" > "$work/failure.log" 2>&1; then
        printf '%s\n' "Unexpected success: $*" >&2
        exit 1
    fi
}

# The source revision and toolchain used in CI must be immutable data.
"$repo/scripts/dbgen-source-pin.sh" > "$work/pin"
printf '%040d\n' 1 > "$work/revision"
printf '1.85.0\n' > "$work/toolchain"
"$repo/scripts/dbgen-source-pin.sh" "$work/revision" "$work/toolchain" > "$work/pin-test"
grep -q '^revision=0000000000000000000000000000000000000001$' "$work/pin-test"
grep -q '^toolchain=1.85.0$' "$work/pin-test"
# shellcheck disable=SC2016 # The command substitution must remain literal data.
for invalid in master latest 1234567 '$(touch unexpected)' '01234567890123456789012345678901234567890g'; do
    printf '%s\n' "$invalid" > "$work/revision"
    expect_failure "$repo/scripts/dbgen-source-pin.sh" "$work/revision" "$work/toolchain"
done
printf '%040d\n' 1 > "$work/revision"
for invalid in stable nightly 1.85 1.85.0.1 1.85.0-x86_64-unknown-linux-gnu; do
    printf '%s\n' "$invalid" > "$work/toolchain"
    expect_failure "$repo/scripts/dbgen-source-pin.sh" "$work/revision" "$work/toolchain"
done
printf '1.85.0\nstable\n' > "$work/toolchain"
expect_failure "$repo/scripts/dbgen-source-pin.sh" "$work/revision" "$work/toolchain"

"$generator" --version
"$generator" convert "$fixtures/source" "$work/base.cbor" --snapshot "$work/base.snapshot"
cmp "$fixtures/base-v1.cbor" "$work/base.cbor"
cmp "$fixtures/base-v1.snapshot" "$work/base.snapshot"

# Both directions use frozen expectations, including unknown optional fields,
# new numeric codes and descriptions that the original runtime cannot execute.
for name in base-v1 newer-v1 descriptions-v1; do
    "$generator" validate "$fixtures/$name.cbor"
    "$generator" dump "$fixtures/$name.cbor" > "$work/$name.json"
    cmp "$fixtures/$name.json" "$work/$name.json"
    "$generator" rewrite "$fixtures/$name.cbor" "$work/$name.cbor" --snapshot "$work/$name.snapshot"
    cmp "$fixtures/$name.cbor" "$work/$name.cbor"
    if [ "$name" != descriptions-v1 ]; then
        cmp "$fixtures/$name.snapshot" "$work/$name.snapshot"
    fi
done
printf '\364' > "$work/prohibited.snapshot"
cmp "$work/prohibited.snapshot" "$work/descriptions-v1.snapshot"

# Every maintained profile participates; the converter must not skip profiles
# excluded by historical check-db's NOCHECKDB handling.
"$generator" convert "$repo/db" "$work/full.cbor" --snapshot "$work/full.snapshot"
"$generator" validate "$work/full.cbor"
"$generator" rewrite "$work/full.cbor" "$work/full-rewrite.cbor" --snapshot "$work/full-rewrite.snapshot"
cmp "$work/full.cbor" "$work/full-rewrite.cbor"
cmp "$work/full.snapshot" "$work/full-rewrite.snapshot"

# Locale, working directory and file discovery order cannot affect output.
mkdir "$work/reordered" "$work/reordered/monitor"
cp "$fixtures/source/options.xml" "$work/reordered/options.xml"
cp "$fixtures/source/monitor/VESA.xml" "$work/reordered/monitor/VESA.xml"
cp "$fixtures/source/monitor/TST0001.xml" "$work/reordered/monitor/TST0001.xml"
for locale in C C.UTF-8 nb_NO.UTF-8 fr_FR.UTF-8; do
    (
        cd "$work"
        LC_ALL="$locale" TZ=Pacific/Honolulu "$generator" convert "$repo/db" full-again.cbor --snapshot full-again.snapshot
        cmp full.cbor full-again.cbor
        cmp full.snapshot full-again.snapshot
        LC_ALL="$locale" "$generator" convert reordered base-again.cbor --snapshot base-again.snapshot
        cmp base.cbor base-again.cbor
        cmp base.snapshot base-again.snapshot
    )
done

# Packaging cannot keep older CBOR beside a newer invalid XML snapshot.
cp -R "$fixtures/source" "$work/broken"
printf '<broken\n' > "$work/broken/monitor/VESA.xml"
printf old > "$work/stale.cbor"
printf old > "$work/stale.snapshot"
expect_failure "$generator" convert "$work/broken" "$work/stale.cbor" --snapshot "$work/stale.snapshot"
[ ! -e "$work/stale.cbor" ]
[ ! -e "$work/stale.snapshot" ]

# Invalid CBOR is rejected before rewrite can publish a replacement.
printf '\241\000' > "$work/truncated.cbor"
expect_failure "$generator" validate "$work/truncated.cbor"
expect_failure "$generator" rewrite "$work/truncated.cbor" "$work/rejected.cbor"
[ ! -e "$work/rejected.cbor" ]

printf '%s\n' 'CBOR producer integration checks passed.'
