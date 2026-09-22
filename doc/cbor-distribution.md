# Candidate-v1 CBOR distribution

The permanent format contract is being reviewed alongside the ddccontrol reader.
This implementation is a candidate, not a published stable v1. XML remains the
maintenance source and both formats are distributed indefinitely. The [format contract](cbor/format.md), [CDDL](cbor/format.cddl),
[coverage](cbor/coverage.md) and [source evidence](cbor/sources.md) are synchronized
with the companion ddccontrol reader. Compatibility changes must update both
repositories before any first v1 publication.

## Tools

Python 3's standard library is the reference producer. No CBOR package is
required. Run commands from the repository root:

```sh
make cbor
python3 scripts/cbor-db.py validate db/ddccontrol-db.cbor
python3 scripts/cbor-db.py dump db/ddccontrol-db.cbor > database.json
python3 scripts/cbor-db.py convert db /tmp/database.cbor --snapshot /tmp/database.snapshot
python3 scripts/cbor-db.py rewrite /tmp/database.cbor /tmp/database-copy.cbor --snapshot /tmp/database-copy.snapshot
make check-cbor
```

`dump` uses `{"$map": [[key, value], ...]}` for every CBOR map and
`{"$bytes": "lowercase hex"}` for every byte string. Thus integer and text keys,
raw bytes and user maps cannot collide. Integers are exact JSON decimal numbers;
consumers must use arbitrary precision JSON parsing for 64-bit values.
`validate` and `rewrite` use strict all-profile reference validation: missing
includes or cycles reject the operation even though the runtime can isolate
those invalid profiles. `rewrite` preserves unknown fields and extensions
byte-for-byte.
It never reconstructs a database through a lossy XML model.

Generation parses every XML profile, including generic IDs, without expanding
includes or interpreting CAPS. Element order and duplicate control definitions
are preserved. Known executable attributes use explicit numeric IDs. Attributes
ignored by the existing reader, such as monitor-control `type`, `name`, `min` and
`max`, are retained in the optional non-executable source-metadata extension.
Non-whitespace source text and unknown elements are retained there as well.
Comments and formatting whitespace do not become active data. Translation
strings remain the original gettext msgids in domain `ddccontrol-db`.

The input manifest contains exact SHA-256 hashes of `options.xml` and every
`monitor/*.xml`. The snapshot identifier is SHA-256 over deterministic CBOR of
that manifest alone. For the baseline XML-equivalent data, its sidecar is those exact manifest CBOR
bytes. If any required extension is present, `fallback_manifest` emits CBOR
`false` (`f4`) instead, permanently forbidding XML fallback if CBOR disappears.
New dual bundles always install this sidecar; they must not omit the guard. Absolute
paths, clocks, file mtimes, locale and machine architecture are absent from the
hash and output. Source files are collected twice and compared to detect a
concurrent change before output. Complete numeric values are retained, including
all 50 current monitor values above 255. Invalid numeric attributes fail the
conversion, including explicitly empty numeric attributes, rather than acquiring
a new default. Empty text attributes and absent attributes remain distinct.

## Build and installation

`make`, `make install` and archive targets all depend on CBOR generation.
Checkouts regenerate on each invocation to catch file deletion and changes that
retain mtimes. A failed generator removes stale CBOR and snapshot artifacts and
stops packaging. Archives carry generated CBOR, snapshot and a source file list;
unmodified archive installations need no Python. An edited archive checks source
inventory and mtimes and requires regeneration. The installed files are
`options.xml`, `monitor/*.xml`, `ddccontrol-db.cbor` and
`ddccontrol-db.snapshot`, plus the same translation catalogues as before.

A new reader chooses files only from the selected data directory. Missing CBOR
uses a pinned XML snapshot, checking the sidecar if supplied. Present invalid or
unsupported CBOR fails with a diagnostic; it does not bypass necessary semantics
through XML. No profile uses common definitions from a different revision.
Existing XML-only packages remain usable. The producer does no hardware I/O.

## Inventory at implementation

At source commit `c0b1a51` there are 466 monitor documents plus `options.xml.in`:
1,077,589 maintained source bytes (1,077,652 with generated `options.xml`), 7 groups, 37 subgroups, 1,744 control elements, 3,726
value elements, 454 includes and 313 CAPS patches. Every XML document parses;
all include targets exist; the deepest include chain has five profiles.
No source control values are changed or omitted. Three existing files contain
stray non-whitespace text that today's reader ignores: `AOC3279.xml` (`-->`),
`BNQ8301.xml` (`-->`) and `DEL40F3.xml` (apostrophe). The metadata extension
preserves this text. Four controls have ignored `min`/`max` attributes, and
monitor-side type attributes include one ignored `boolean` value.

After the final inactive-subtree preservation fix, the initial snapshot encodes
to 311,775 bytes. The final upstream source rebase (`c4f616e`, `VERSION=20260922`)
contains 470 profiles and encodes to 313,219 bytes; see
[producer validation](cbor/producer-validation.md) for its exact identity. This is a
file-size observation, not a claim about reader memory or speed. Actual Rust
reader measurements and semantic-equivalence tests belong to the companion
reader change. Producer tests assert every source attribute and element order,
but do not replace runtime semantic testing.

## Source-encoding boundary

The reference converter accepts UTF-8, BOM-marked UTF-16, Windows-1252 and
ISO-8859-1/ASCII aliases with the Rust reader's WHATWG Windows-1252 interpretation.
It accepts existing leading whitespace/comments before an XML declaration.
Other declared encodings are explicitly rejected until equivalent decoding is
implemented and tested; no differently decoded profile is silently emitted.
DTDs/entities and malformed input are rejected. This is a documented coverage
gap against the reader's broader encoding_rs label set, not a wire limitation.
All current source profiles are within the supported set.
