# Building and using the CBOR producer

The `ddccontrol-dbgen` Rust executable lives in the ddccontrol repository. It
shares XML decoding, the format validator and deterministic CBOR encoding with
the reader. This repository maintains XML and translation sources, immutable
compatibility fixtures and integration checks. It does not maintain a second
implementation of those rules.

This producer step does not change the default `make`, installation or release
archive contents. Permanent dual-format build/install integration is tracked
separately in [PR #439](https://github.com/ddccontrol/ddccontrol-db/pull/439), which
must use this generator interface when rebased. XML remains maintained and
installed with no retirement date.

## Local generation and validation

Use an installed `ddccontrol-dbgen`, an unpacked release artifact for the build
machine's architecture, or an explicitly selected local executable. Generating
CBOR requires no network access, Python, monitor connection or monitor writes:

```sh
make db/options.xml
mkdir -p build/cbor
ddccontrol-dbgen convert db build/cbor/ddccontrol-db.cbor \
    --snapshot build/cbor/ddccontrol-db.snapshot
ddccontrol-dbgen validate build/cbor/ddccontrol-db.cbor
ddccontrol-dbgen dump build/cbor/ddccontrol-db.cbor
make check-cbor
```

The revision defaults to the generated `options.xml` date. `--revision TEXT`
sets an explicit database revision without changing the source snapshot hash.
`rewrite INPUT OUTPUT --snapshot PATH` validates and preserves unknown optional
fields and required extensions. If a file needs semantics outside the XML
reader's model, its sidecar is the permanent CBOR `false` fallback guard.
Generation failure removes the requested CBOR and sidecar outputs, preventing
reuse of stale data beside a newer XML source snapshot.

For an executable outside `PATH`:

```sh
make check-cbor DDCDBGEN=/absolute/path/to/ddccontrol-dbgen
/absolute/path/to/ddccontrol-dbgen convert db build/cbor/ddccontrol-db.cbor \
    --snapshot build/cbor/ddccontrol-db.snapshot
```

`make check-cbor` requires a POSIX shell and ordinary Unix utilities in addition
to the executable. It checks every maintained profile, including historical
`NOCHECKDB` profiles. Full Rust unit, malformed-input and semantic differential
tests run in the companion source checkout in CI.

## CI uses a pinned source build

[`.ci/ddccontrol-dbgen.rev`](../../.ci/ddccontrol-dbgen.rev) is a complete,
immutable commit SHA in `ddccontrol/ddccontrol`.
[`.ci/ddccontrol-dbgen.toolchain`](../../.ci/ddccontrol-dbgen.toolchain) records
a numeric Rust release. Neither may be a moving branch, `latest` or `stable`.
CI validates these data files before using them, checks out the exact source,
checks the resulting `HEAD`, then runs Cargo with `--locked`. It builds only
the generator and relevant Rust libraries; no GUI or C application build is
needed. Dependency and target caches accelerate the next run; Cargo still
checks the selected source and lockfile.

To build locally from an already obtained ddccontrol checkout:

```sh
# Run in ddccontrol-db. This prints revision/toolchain data; it is not shell code.
./scripts/dbgen-source-pin.sh
# Check out that revision in a separate ddccontrol source checkout, then:
cd /path/to/ddccontrol
cargo +1.85.0 build --locked --release -p ddccontrol-dbgen
```

Database updates do not require a new ddccontrol release. A generator change
uses a companion ddccontrol PR: push its reviewed implementation, update the
full SHA here, and run both repositories' checks. Before merging the database
PR, merge the companion PR and update this pin to the resulting permanent
upstream commit if squash/rebase changed its identity. Re-run CI after that
update. Routine monitor-only PRs retain the existing generator pin.

A published standalone artifact is an alternative for developers and packagers,
not an implicit CI input. Select an exact release, correct architecture and
verify its published SHA-256 checksum. No command here downloads the newest
binary automatically.

## Distribution and offline builds

A generator pin is provenance, not a request for network access during normal
`make` or a Debian package build. An offline packager must provide the executable
as a build dependency, or build it ahead of time using the pinned source and
available Rust dependencies. Debian's packaged Rust crates and dependency
policy still apply; an upstream `Cargo.lock` alone does not make those crates
available offline.

The subsequent packaging integration must place generated CBOR, its matching
sidecar, XML and translations from one snapshot in distribution archives.
Installing such an archive must not require Cargo or the generator. Regenerating
changed XML must require an available generator and fail on errors instead of
retaining older CBOR. This producer-only change deliberately leaves those
archive and installation rules to the separate packaging PR.
