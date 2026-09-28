#!/bin/sh
# Exercise the package build with real conversion and temporary source trees.
set -eu
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd)
generator=$(command -v "${DDCDBGEN:-ddccontrol-dbgen}")
case "$generator" in
    /*) ;;
    *) generator="$(CDPATH='' cd -- "$(dirname -- "$generator")" && pwd)/$(basename -- "$generator")" ;;
esac
make_command=${MAKE:-make}
# Each test selects its own generator; parent make overrides must not leak in.
unset DDCDBGEN MAKEFLAGS MFLAGS MAKEOVERRIDES

work=$(mktemp -d "${TMPDIR:-/tmp}/ddccontrol-db-build-test.XXXXXXXX")
trap 'rm -rf "$work"' EXIT
trap 'exit 1' HUP INT TERM
mkdir -p "$work/source/build-aux" "$work/source/.ci" "$work/source/po"
cp "$repo/Makefile" "$repo/configure" "$repo/configure.impl" "$repo/VERSION" "$work/source/"
cp "$repo/build-aux/make-config.sh" "$repo/build-aux/build-cbor.sh" "$work/source/build-aux/"
cp "$repo/.ci/ddccontrol-dbgen.rev" "$work/source/.ci/"
cp -R "$repo/tests/cbor/fixtures/source" "$work/source/db"
cp "$work/source/db/options.xml" "$work/source/db/options.xml.in"
touch "$work/source/db/options.xml"
: > "$work/source/po/LINGUAS"

expect_failure()
{
    if "$@" > "$work/failure.log" 2>&1; then
        printf '%s\n' "Unexpected success: $*" >&2
        exit 1
    fi
}

assert_no_artifacts()
{
    test ! -e db/ddccontrol-db.cbor
    test ! -e db/ddccontrol-db.snapshot
    test ! -e db/ddccontrol-db.sources
}

# A quoted executable path selected at configure time survives an unset
# environment at make time. The marker distinguishes it from a PATH default.
configured_generator="$work/configured generator's executable"
cat > "$configured_generator" <<'EOF'
#!/bin/sh
set -eu
: > "$GENERATOR_MARKER"
exec "$REAL_GENERATOR" "$@"
EOF
chmod +x "$configured_generator"
REAL_GENERATOR=$generator
GENERATOR_MARKER="$work/generator-used"
export REAL_GENERATOR GENERATOR_MARKER
cd "$work/source"
DDCDBGEN="$configured_generator" ./configure --prefix=/usr --disable-nls
"$make_command" cbor
test -f "$GENERATOR_MARKER"
cmp "$repo/tests/cbor/fixtures/base-v1.cbor" db/ddccontrol-db.cbor
cmp "$repo/tests/cbor/fixtures/base-v1.snapshot" db/ddccontrol-db.snapshot

# Environment and command-line selections override the saved generator.
rm db/ddccontrol-db.cbor "$GENERATOR_MARKER"
expect_failure env DDCDBGEN="$work/missing" "$make_command" cbor
assert_no_artifacts
DDCDBGEN="$generator" "$make_command" cbor
test ! -e "$GENERATOR_MARKER"
rm db/ddccontrol-db.cbor
expect_failure "$make_command" cbor DDCDBGEN="$work/missing"
assert_no_artifacts
"$make_command" cbor DDCDBGEN="$generator"
test ! -e "$GENERATOR_MARKER"
./configure --prefix=/usr --disable-nls "DDCDBGEN=$configured_generator"
rm db/ddccontrol-db.cbor
"$make_command" cbor
test -f "$GENERATOR_MARKER"

# Unmodified archive sources install without a generator or gettext.
"$make_command" install DDCDBGEN="$work/missing" MSGFMT=false "DESTDIR=$work/stage"
installed="$work/stage/usr/share/ddccontrol-db"
cmp db/ddccontrol-db.cbor "$installed/ddccontrol-db.cbor"
cmp db/ddccontrol-db.snapshot "$installed/ddccontrol-db.snapshot"
cmp db/monitor/VESA.xml "$installed/monitor/VESA.xml"

# A downstream patch can keep the old timestamp; both monitor and common
# option edits must invalidate archive reuse and stop installation.
for file in db/monitor/VESA.xml db/options.xml; do
    cp -p "$file" "$work/original.xml"
    sed 's/address="0x10"/address="0x11"/' "$work/original.xml" > "$file"
    touch -r "$work/original.xml" "$file"
    if cmp -s "$work/original.xml" "$file"; then exit 1; fi
    expect_failure "$make_command" install DDCDBGEN="$work/missing" "DESTDIR=$work/rejected"
    assert_no_artifacts
    test ! -e "$work/rejected"
    "$make_command" cbor
    if cmp -s "$repo/tests/cbor/fixtures/base-v1.cbor" db/ddccontrol-db.cbor; then exit 1; fi
    cp -p "$work/original.xml" "$file"
    "$make_command" cbor
done

# Additions and removals also invalidate the source manifest.
cp -p db/monitor/VESA.xml db/monitor/TST0002.xml
expect_failure "$make_command" cbor DDCDBGEN="$work/missing"
assert_no_artifacts
"$make_command" cbor
rm db/monitor/TST0002.xml
expect_failure "$make_command" cbor DDCDBGEN="$work/missing"
assert_no_artifacts
"$make_command" cbor

# Distribution sources come from Git, so an untracked local profile must
# stay out of both the packaged XML and its generated CBOR artifacts.
git init -q .
git add Makefile configure configure.impl VERSION build-aux .ci po db/options.xml.in db/monitor
cp -p db/monitor/VESA.xml db/monitor/TST0002.xml
./configure --prefix=/usr --disable-nls "DDCDBGEN=../configured generator's executable"
"$make_command" dist-gzip MSGFMT=false
version=$(sed -n '1p' VERSION)
mkdir "$work/release"
tar -xzf "ddccontrol-db-$version.tar.gz" -C "$work/release"
distributed="$work/release/ddccontrol-db-$version"
test ! -e "$distributed/db/monitor/TST0002.xml"
cmp "$repo/tests/cbor/fixtures/base-v1.cbor" "$distributed/db/ddccontrol-db.cbor"
cmp "$repo/tests/cbor/fixtures/base-v1.snapshot" "$distributed/db/ddccontrol-db.snapshot"
(
    cd "$distributed"
    ./configure --prefix=/usr --disable-nls "DDCDBGEN=$work/missing"
    "$make_command" install MSGFMT=false "DESTDIR=$work/release-stage"
)
cmp "$distributed/db/ddccontrol-db.cbor" "$work/release-stage/usr/share/ddccontrol-db/ddccontrol-db.cbor"
test ! -e "$work/release-stage/usr/share/ddccontrol-db/monitor/TST0002.xml"
rm db/monitor/TST0002.xml

# Model a reader that prefers cached CBOR, then examines XML if CBOR is absent.
# check-db must still reject the edited XML without deleting the build outputs.
cat > "$work/validator" <<'EOF'
#!/bin/sh
set -eu
test "$1" = -b
if test -f "$2/ddccontrol-db.cbor"; then exit 0; fi
if grep -q '<broken' "$2/monitor/TST0001.xml"; then
    echo 'Invalid current XML' >&2
    exit 1
fi
EOF
chmod +x "$work/validator"
"$make_command" check-db "DDCCONTROL=$work/validator"
printf '<broken\n' > db/monitor/TST0001.xml
expect_failure "$make_command" check-db "DDCCONTROL=$work/validator"
grep -q 'Invalid current XML' "$work/failure.log"
test -f db/ddccontrol-db.cbor
expect_failure "$make_command" cbor
assert_no_artifacts

printf '%s\n' 'CBOR build and installation regression checks passed.'
