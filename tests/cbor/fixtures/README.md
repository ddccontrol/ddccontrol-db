# Frozen candidate-v1 fixtures

These files were frozen with the initial candidate on 2026-09-22. Tests consume
these committed bytes; they never regenerate expected outputs. The producer is
required to reproduce them from the committed source files. Do not update the
binary merely to make a changed encoder pass.

* `base-v1.cbor`: 850-byte database, two profiles (`TST0001`, generic `VESA`).
* `base-v1.snapshot`: the exact deterministic CBOR source manifest (root field 8).
* `base-v1.json`: exact decoded content in the documented typed JSON dump form.
* `source/`: independent frozen XML inputs, including original comments.

The fixture covers ordered CAPS add/remove and include operations, a 16-bit
`0xFFA3` value, UTF-8 `Écran`, zero delay versus omitted delay, ignored XML
attributes stored as inert metadata, and a commented control that remains
inactive. Snapshot ID:
`1a5d22754252788a42720b9661dd7e7a1ee3e000e654e634014c4b66e53489f0`.

RFC 8949 integer/string/container vectors are also fixed inline in
`test_cbor.py`. The independent Rust reader in the companion ddccontrol change
consumes the same binary; this is stronger than a producer self-roundtrip.

* `descriptions-v1.cbor` and `.json`: frozen future descriptor example built on
  the unchanged base fixture. Root optional field 100 carries examples of all
  six descriptive categories. `TST0001` has a required profile descriptor with
  matchers, six declarative operation classes, full-width/binary/symbolic
  values, rational step, hardware-discovered maximum, bitfield layout, version
  identities, raw CAPS, command codes, conditions and opaque descriptor bytes.
  None are hardware observations. The initial reader must reject `TST0001`
  and keep the unaffected `VESA` profile usable.
* `description-payload.cbor`: the exact profile descriptor payload alone,
  allowing independent CDDL validation against `function-description`.

* `newer-v1.cbor`, `.json`, `.snapshot` and `newer-source/`: subsequent compatible
  database revision `fixture-2`, with unchanged `TST0001` and `VESA` profiles,
  new `NEW0001` profile and `vendor_future` list definition. VCP code `0xFE`
  has the full 16-bit choice `65535`. Root field 10, profile field 4, and an
  optional control extension carry unknown inert data. The frozen original
  reader must construct known and new profiles without decoder changes.
