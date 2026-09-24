# Producer validation

## Producer PR verification, 2026-09-24

The producer PR was rebased onto `401025e` after the format-contract PR merged.
This step adds the standalone tools and their CI job; CBOR build/install targets
belong to the subsequent packaging PR. Run its tests from the repository root:

```sh
make db/options.xml
python3 -m unittest discover -s tests/cbor -v
```

On Linux x86_64 with Python 3.14.4:

* All 27 producer tests pass, including regression cases for unknown node kinds
  prohibiting XML fallback, invalid identity text, and long numeric literals.
  Leading-zero values remain valid; overflow reports the source file and field.
* `./configure --prefix=/usr` and `make -j2 check check-controls` pass, including
  all 51 list-checker regression subtests.
* All 470 profiles convert to the same 313,219 bytes, file SHA-256 and source
  snapshot recorded below. No frozen XML, CBOR or JSON fixture was changed.
* Independent `cddl-cat` 0.7.1 validation accepts the complete generated database
  and the base, newer-database and future-description fixtures.
* The Rust reader's `whole_database_xml_cbor_semantics_match_when_configured`
  test passes with this converter: 470 profiles × 3 CAPS inputs × strict/tolerant
  modes, comparing complete trees, CAPS and failure status between XML and CBOR.
  It was run with gettext enabled in ddccontrol `24f2868`, using absolute
  `DDCCONTROL_DB_TEST_DATADIR` and `DDCCONTROL_DB_CONVERTER` paths.
* A C probe linked to the unchanged first-reader library rejects a profile with
  an unknown node kind. After removing CBOR, it also rejects initialization from
  the producer's guarded XML sidecar. Invalid extension identity text is now
  rejected by both producer and reader.

These checks perform no monitor operations. Architecture execution and memory
measurements were not rerun for this producer review.

## Combined implementation record, 2026-09-22

The following historical checks ran before the changes were split into PRs.
They include the build/install integration supplied separately by the packaging
PR; `make check-cbor` and dual-format archives are not part of this producer-only
step.

Source baseline: `ddccontrol-db` commit `c4f616e`, `VERSION=20260922`.
Host: Linux x86_64, Python 3.14.4. This is an unpublished candidate review;
no release was created.

The maintained sources have 470 monitor XML files plus `options.xml.in` and
1,099,739 bytes. Generated `options.xml` adds its existing warning and replaces
`$DATE`, giving 1,099,802 exact manifest-input bytes. Every source profile is
converted. The four profiles added by the final upstream rebase are
`DEL427D`, `DEL427E`, `DEL427F`, and `GBT2709`. The CBOR file is 313,219 bytes and its manifest snapshot is
`dbb9f1542128e579f61dc8147c03c2f72eb5220d0c31e7961c001516942656b9`.

The full-file SHA-256 is
`8315983f0ca09e8230e3cbb92b71e4cb5f0fa780634fa33a47179eb4ce36c813`.

Executed successfully:

* `./configure --prefix=/usr`, GNU `make -j2`, `make check`.
* `make check-controls`: all 470 profiles pass with 30 preexisting grandfathered
  empty-list exceptions; 51 checker regression subtests pass.
* `make check-cbor`: 23 Python test methods pass, including all attributes/order
  for the complete database, 850 distinct truncations, malicious CBOR vectors,
  golden fixtures, numeric grammar, 16-bit values, encoding/prefix compatibility,
  unknown inert data, inactive descendants, namespaces, descriptor type
  validation and guarded XML fallback.
* `make check-db DDCCONTROL=/usr/local/bin/ddccontrol` with the installed
  pre-CBOR ddccontrol 3.3.0: 934 successful integrity checks (options plus 467
  profiles). That existing target skips three `NOCHECKDB` profiles; the new
  converter and whole-source tests include all three. This uses integrity
  mode and sends no commands to a monitor.
* `make dist-xz`; configure/build/staged install from the extracted archive with
  `PYTHON=false MSGFMT=false`: CBOR, source manifest, all 470 XML profiles and
  French translations match. Removing an XML profile then running make without
  Python fails and removes stale CBOR and sidecar outputs.
* BSD bmake 20200710 (Ubuntu package 20200710-17build1, unpacked locally): parallel
  build, `check`, `check-cbor` and staged `install LINGUAS=fr` passed on the
  initial 466-profile baseline before the final source rebase.
* Four locale settings (`C`, `C.UTF-8`, `nb_NO.UTF-8`, `fr_FR.UTF-8`) and an
  unrelated current directory produce both the frozen fixture and the final
  complete 470-profile database byte-for-byte.
  Python's converter does not require those system locales to be installed.

The independent Rust reader consumes these fixtures and compares actual monitor
trees, CAPS and errors across XML/CBOR. Actual Rust memory/timing and s390x
execution results are reported in the companion ddccontrol PR; they must not be
inferred from this producer's file-size observation or Python allocations.

The shared CDDL was independently parsed and used to validate the initial
complete CBOR file and frozen examples with `cddl-cat` 0.7.1 in the companion repository.
The `function-description` entry also validates the standalone frozen descriptor
payload. Remaining source-standard and legacy-encoding gaps are explicit in
[coverage](coverage.md#inventory-and-evidence) and [sources](sources.md).
