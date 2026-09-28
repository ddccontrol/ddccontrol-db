# Candidate-v1 CBOR distribution

The format contract is being reviewed alongside the ddccontrol reader. This is
an unpublished candidate. XML remains the maintained source and both formats
are distributed indefinitely. The [format contract](cbor/format.md),
[CDDL](cbor/format.cddl), [coverage](cbor/coverage.md) and
[source evidence](cbor/sources.md) describe the shared producer/reader rules.
Compatibility changes must update both repositories before a first v1 release.

## Tools

`ddccontrol-dbgen` is the standalone Rust producer from ddccontrol. It shares
XML decoding, validation and deterministic encoding with the reader; no Python
implementation is used. See [producer setup](cbor/producer.md) for pinned source
builds, prebuilt executables and offline packaging. From the repository root:

```sh
DDCDBGEN=/absolute/path/to/ddccontrol-dbgen ./configure
make cbor
make check-cbor
# With the generator on PATH:
ddccontrol-dbgen validate db/ddccontrol-db.cbor
ddccontrol-dbgen dump db/ddccontrol-db.cbor > database.json
ddccontrol-dbgen convert db /tmp/database.cbor --snapshot /tmp/database.snapshot
ddccontrol-dbgen rewrite /tmp/database.cbor /tmp/database-copy.cbor --snapshot /tmp/database-copy.snapshot
```

Configure saves the selected executable. Environment and make command-line
`DDCDBGEN` settings override that selection, including for `make check-cbor`.
Normal builds never download a generator or Rust dependencies.

`dump` uses typed JSON for CBOR maps and byte strings; `rewrite` preserves
unknown fields and extensions. The [producer validation record](cbor/producer-validation.md)
describes immutable fixtures, full-database checks and runtime equivalence
coverage. Producer operations and packaging tests perform no monitor I/O.

## Build and installation

`make`, `make install` and archive targets depend on CBOR generation. Git
checkouts regenerate on each invocation. Archives carry CBOR, its sidecar and
`ddccontrol-db.sources`, a SHA-256 manifest of every XML input and the generator
source pin. Reuse compares content hashes and the complete filename inventory;
mtime-preserving edits, additions and deletions all require regeneration.
Installation needs a SHA-256 utility (`sha256sum`, `sha256` or `shasum`). An
unmodified archive requires no generator, Cargo, Python or gettext.

Archive targets generate CBOR and its manifests from the staged distribution
XML. Untracked local profiles are excluded from both formats in the archive.

A failed build removes stale CBOR, snapshot and source-manifest outputs and
stops packaging, including when the generator cannot start. A source change
during generation also fails the build. The generator atomically replaces each
successful output. Packaging tools should stage an entire installation before
replacing the installed database.

The installed files are `options.xml`, `monitor/*.xml`, `ddccontrol-db.cbor`
and `ddccontrol-db.snapshot`, plus the existing translation catalogues.
`ddccontrol-db.sources` is build metadata and is not installed. XML and gettext
sources remain maintained in this repository.

`make check-db` validates a temporary XML-only copy with the chosen ddccontrol
executable. Previously generated CBOR therefore cannot hide a broken or newly
edited XML profile. This target does not need the generator. `make check-cbor`
uses the generator for frozen fixtures, full-database checks, reproducibility
and regression tests of archive reuse, configuration and installation.

## Reader fallback

The installed sidecar authorizes XML fallback only for an equivalent legacy XML
snapshot. A manifest records exact SHA-256 source hashes; the CBOR value `false`
forbids fallback when definitions require additional semantics. Every dual
bundle installs this sidecar. See the format contract for the complete rules.

A reader chooses files only from its selected directory and pins its chosen
snapshot for the load session. Present invalid or unsupported CBOR fails with a
diagnostic. When CBOR is absent, fallback must satisfy the sidecar; existing
XML-only packages without a sidecar remain supported.
