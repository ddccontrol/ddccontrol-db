import hashlib
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/cbor"))
from codec import Invalid, decode, diagnostic, encode
from model import ATTRS, KINDS, METADATA, convert, fallback_manifest, integer, load, validate

FIXTURES = Path(__file__).parent / "fixtures"


class CodecTests(unittest.TestCase):
    def test_reference_vectors(self):
        vectors = [(0, "00"), (23, "17"), (24, "1818"), (255, "18ff"),
                   (256, "190100"), (65535, "19ffff"), (65536, "1a00010000"),
                   (2**64 - 1, "1bffffffffffffffff"), (-2**64, "3bffffffffffffffff"),
                   (-1, "20"), (b"\xff\x00", "42ff00"), ("é", "62c3a9"),
                   ([False, True, None], "83f4f5f6"),
                   ({24: 0, "": 0}, "a21818006000")]
        for value, wire in vectors:
            with self.subTest(wire=wire):
                self.assertEqual(encode(value).hex(), wire)
                self.assertEqual(decode(bytes.fromhex(wire)), value)

    def test_adversarial_vectors(self):
        cases = {"truncated": "1a0000", "trailing": "0000", "duplicate": "a200000001",
                 "unordered": "a201000000", "utf8": "61ff", "tag": "c000",
                 "float": "fa00000000", "bignum": "c24101", "indefinite": "9fff",
                 "non-shortest": "1800", "huge array": "9bffffffffffffffff",
                 "huge text": "7bffffffffffffffff", "undefined": "f7",
                 "negative key": "a12000", "boolean key": "a1f500",
                 "deep": "81" * 65 + "00", "reserved": "1c"}
        for reason, wire in cases.items():
            with self.subTest(reason=reason), self.assertRaises(Invalid):
                decode(bytes.fromhex(wire))

    def test_every_truncation(self):
        wire = (FIXTURES / "base-v1.cbor").read_bytes()
        for length in range(len(wire)):
            with self.subTest(length=length), self.assertRaises(Invalid):
                decode(wire[:length])

    def test_unambiguous_json(self):
        value = {1: b"\x01", "1": {"$bytes": "01"}, 2: -2**64}
        self.assertEqual(diagnostic(value), {"$map": [[1, {"$bytes": "01"}],
                          ["1", {"$map": [["$bytes", "01"]]}], [2, -2**64]]})


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "source"
        shutil.copytree(FIXTURES / "source", self.source)

    def test_frozen_fixture(self):
        data = (FIXTURES / "base-v1.cbor").read_bytes()
        database = load(data)
        self.assertEqual(encode(convert(self.source)), data)
        self.assertEqual(diagnostic(database), json.loads((FIXTURES / "base-v1.json").read_text()))
        self.assertEqual(encode(database[8]), (FIXTURES / "base-v1.snapshot").read_bytes())

    def test_entire_database_attributes_and_order(self):
        database = convert(REPO / "db")
        self.assertEqual(len(database[6]), len(list((REPO / "db/monitor").glob("*.xml"))))
        reverse_attrs = {v: k for k, v in ATTRS.items()}
        def compare(element, node):
            self.assertEqual(node[0], KINDS.get(element.tag, 255))
            preserved = {reverse_attrs[k]: v for k, v in node[1].items()}
            for ext in node.get(3, []):
                self.assertEqual(ext[0], METADATA)
                preserved.update(ext[2].get(0, {}))
            self.assertEqual(set(preserved), set(element.attrib))
            for key, value in element.attrib.items():
                if isinstance(preserved[key], int):
                    self.assertEqual(preserved[key], int(value, 16 if value.lower().startswith("0x") else 10))
                else:
                    self.assertEqual(preserved[key], value)
            self.assertEqual(len(node[2]), len(list(element)))
            for child, encoded in zip(element, node[2]):
                compare(child, encoded)
        compare(ET.parse(REPO / "db/options.xml").getroot(), database[5])
        for identifier, node in database[6].items():
            compare(ET.parse(REPO / "db/monitor" / (identifier + ".xml")).getroot(), node)
        self.assertEqual(load(encode(database)), database)

    def test_reproducible_locale_and_working_directory(self):
        output = Path(self.temp.name) / "out.cbor"
        baseline = (FIXTURES / "base-v1.cbor").read_bytes()
        for locale in ("C", "C.UTF-8", "nb_NO.UTF-8", "fr_FR.UTF-8"):
            result = subprocess.run([sys.executable, str(REPO / "scripts/cbor-db.py"), "convert",
                                     str(self.source), str(output)], cwd="/", capture_output=True,
                                    env={**os.environ, "LANG": locale, "LC_ALL": locale})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_bytes(), baseline)

    def test_legacy_encoding_comments_and_ignored_attributes(self):
        profile = self.source / "monitor/TST0001.xml"
        profile.write_bytes(b'<?xml version="1.0" encoding="ISO-8859-1"?><monitor name="\xe9"><controls><control id="brightness" address="0" delay="0" default="12"/><control id="brightness" address="16"/></controls><!-- ignored --><future flag="1"/></monitor>')
        db = convert(self.source)
        node = db[6]["TST0001"]
        self.assertEqual(node[1][0], "é")
        first, second = node[2][0][2]
        self.assertEqual(first[1][6], 0)
        self.assertEqual(first[1][7], 0)
        self.assertNotIn(7, second[1])
        self.assertEqual(first[3][0][2][0], {"default": "12"})
        self.assertEqual(node[2][1][0], 255)
        self.assertEqual(len(node[2]), 2)

    def test_out_of_context_known_elements_keep_attributes_inert(self):
        profile = self.source / "monitor/VESA.xml"
        profile.write_text('<monitor name="Generic"><control id="brightness" address="0x10"/><controls><control id="brightness" address="0x10"/></controls></monitor>')
        nodes = convert(self.source)[6]["VESA"][2]
        self.assertEqual(nodes[0][1], {})
        self.assertEqual(nodes[0][3][0][2][0], {"id": "brightness", "address": "0x10"})
        self.assertEqual(nodes[1][2][0][1], {1: "brightness", 6: 16})

    def test_inactive_branches_never_activate_or_validate_descendants(self):
        profile = self.source / "monitor/VESA.xml"
        profile.write_text('<monitor name="Generic"><control id="brightness" address="invalid"><value id="wide" value="invalid"/></control><future><monitor><include file="MISSING"/><controls><control id="brightness" address="invalid"/></controls></monitor></future><controls><control id="brightness" address="16"/></controls></monitor>')
        tree = convert(self.source)[6]["VESA"]
        direct_control, unknown_branch, active_controls = tree[2]
        self.assertEqual(direct_control[1], {})
        self.assertEqual(direct_control[2][0][1], {})
        self.assertEqual(direct_control[2][0][3][0][2][0]["value"], "invalid")
        nested_monitor = unknown_branch[2][0]
        self.assertEqual(nested_monitor[2][0][1], {})
        self.assertEqual(nested_monitor[2][0][3][0][2][0]["file"], "MISSING")
        self.assertEqual(active_controls[2][0][1][6], 16)

    def test_namespaced_elements_use_local_name_but_attributes_do_not(self):
        profile = self.source / "monitor/VESA.xml"
        profile.write_text('<n:monitor xmlns:n="urn:example:xml" name="Generic"><n:controls><n:control id="brightness" address="16" n:address="invalid"><n:value id="wide" value="65535" n:value="invalid"/></n:control></n:controls></n:monitor>')
        tree = convert(self.source)[6]["VESA"]
        self.assertEqual(tree[0], 5)
        control = tree[2][0][2][0]
        self.assertEqual(control[0], 3)
        self.assertEqual(control[1][6], 16)
        self.assertEqual(control[2][0][1][8], 65535)
        self.assertEqual(control[3][0][2][0], {"{urn:example:xml}address": "invalid"})
        self.assertEqual(control[2][0][3][0][2][0], {"{urn:example:xml}value": "invalid"})

    def test_utf16_and_doctype_handling(self):
        profile = self.source / "monitor/VESA.xml"
        xml = '<?xml version="1.0" encoding="UTF-16"?><monitor name="Écran"/>'
        profile.write_bytes(xml.encode("utf-16"))
        self.assertEqual(convert(self.source)[6]["VESA"][1][0], "Écran")
        xml = '<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE monitor [<!ENTITY label "name">]><monitor name="&label;"/>'
        profile.write_bytes(xml.encode("utf-16"))
        with self.assertRaises(Invalid):
            convert(self.source)

    def test_legacy_declaration_prefix_and_windows_encoding(self):
        profile = self.source / "monitor/VESA.xml"
        profile.write_bytes(b' \n<!-- old prefix -->\n<?xml version="1.0" encoding="ISO-8859-1"?><monitor name="\x80cran"/>')
        self.assertEqual(convert(self.source)[6]["VESA"][1][0], "€cran")
        profile.write_bytes(b'<?xml version="1.0" encoding="unknown-encoding"?><monitor name="x"/>')
        with self.assertRaisesRegex(Invalid, "unsupported source XML encoding"):
            convert(self.source)

    def test_missing_reference_and_cycle(self):
        profile = self.source / "monitor/VESA.xml"
        for target in ("MISSING", "TST0001"):
            profile.write_text('<monitor name="Generic"><include file="' + target + '"/></monitor>')
            with self.assertRaises(Invalid):
                convert(self.source)

    def test_legacy_numeric_grammar(self):
        for raw, expected in (("020", 16), ("+0x10", 16), ("  +016", 14), ("000", 0)):
            self.assertEqual(integer(raw, "address"), expected)
        self.assertEqual(integer("020", "delay"), 20)
        self.assertEqual(integer(" -10", "delay"), -10)
        for raw, attr in (("08", "address"), ("16 ", "address"), ("0x10", "delay"),
                          ("", "value"), ("1_0", "value"), ("\u00a016", "address")):
            with self.subTest(raw=raw, attr=attr), self.assertRaises(Invalid):
                integer(raw, attr)

    def test_long_numeric_literals(self):
        self.assertEqual(integer("0" * 5000, "delay"), 0)
        self.assertEqual(integer("0" * 5000 + "1", "delay"), 1)
        profile = self.source / "monitor/VESA.xml"
        profile.write_text('<monitor name="Generic"><controls><control id="brightness" address="'
                           + "1" * 5000 + '"/></controls></monitor>')
        with self.assertRaisesRegex(Invalid, "monitor/VESA.xml: address outside normative range"):
            convert(self.source)

    def test_newer_database_keeps_original_profiles_and_new_numeric_semantics(self):
        base = load((FIXTURES / "base-v1.cbor").read_bytes())
        newer = load((FIXTURES / "newer-v1.cbor").read_bytes())
        self.assertEqual(diagnostic(newer), json.loads((FIXTURES / "newer-v1.json").read_text()))
        for identifier in ("VESA", "TST0001"):
            self.assertEqual(newer[6][identifier], base[6][identifier])
        control = newer[6]["NEW0001"][2][1][2][0]
        self.assertEqual(control[1][6], 254)
        self.assertEqual(control[2][0][1][8], 65535)
        self.assertIs(control[3][0][1], False)
        self.assertEqual(encode(fallback_manifest(newer)), (FIXTURES / "newer-v1.snapshot").read_bytes())
        produced = convert(FIXTURES / "newer-source")
        produced[10] = newer[10]
        produced[6]["NEW0001"][4] = newer[6]["NEW0001"][4]
        produced[6]["NEW0001"][2][1][2][0][3] = control[3]
        self.assertEqual(encode(produced), (FIXTURES / "newer-v1.cbor").read_bytes())

    def test_descriptive_types_and_necessary_matcher_fixture(self):
        db = load((FIXTURES / "descriptions-v1.cbor").read_bytes())
        self.assertEqual(diagnostic(db), json.loads((FIXTURES / "descriptions-v1.json").read_text()))
        ext = db[6]["TST0001"][3][0]
        self.assertIs(ext[1], True)
        self.assertNotIn(3, db[6]["VESA"])
        self.assertEqual(ext[2], decode((FIXTURES / "description-payload.cbor").read_bytes()))
        self.assertEqual([x[2][0] for x in db[100]], [1, 2, 3, 4, 5, 6])
        for key, value in ((0, 7), (1, 4), (4, 256), (8, {0: 1, 1: {0: 1, 1: 0}}),
                           (9, {0: 2, 1: 12}), (11, [{0: 0, 1: 65}]),
                           (16, [{0: "urn:a", 1: "urn:b", 2: "not bytes"}])):
            bad = copy.deepcopy(db)
            bad[6]["TST0001"][3][0][2][key] = value
            with self.subTest(key=key), self.assertRaises(Invalid):
                validate(bad)

    def test_metadata_contract_and_duplicate_extensions(self):
        db = convert(self.source)
        for extension in ({0: METADATA, 1: True, 2: {0: {}}},
                          {0: METADATA, 1: False, 2: {}},
                          {0: METADATA, 1: False, 2: {0: {"x": 3}}}):
            db[7] = [extension]
            with self.assertRaises(Invalid):
                validate(db)
        db[7] = [{0: "urn:example:future", 1: False, 2: None}] * 2
        with self.assertRaises(Invalid):
            validate(db)

    def test_extension_identity_grammar(self):
        db = convert(self.source)
        description = "https://ddccontrol.sourceforge.net/cbor/ext/function-description/1"
        for identity in ("urn:example:bad identity", "urn:example:\n", "urn:example:\0",
                         "urn:example:\x7f", "urn:example:\x80", "urn:example:\u00a0",
                         "urn:example:\u2003", "relative", "1scheme:value", "", None, 1):
            for extension in ({0: identity, 1: False, 2: None},
                              {0: description, 1: False, 2: {3: identity}},
                              {0: description, 1: False, 2: {18: [{0: identity, 1: False, 2: None}]}}):
                db[7] = [extension]
                with self.subTest(identity=identity, extension=extension), self.assertRaises(Invalid):
                    load(encode(db))
        for identity in ("urn:example:feature:1", "https://example.org/feature%20name/1",
                         "SCHEME+name.test-1:payload"):
            db[7] = [{0: identity, 1: False, 2: None},
                     {0: description, 1: False, 2: {3: identity}}]
            self.assertEqual(load(encode(db)), db)

    def test_numeric_ranges(self):
        profile = self.source / "monitor/VESA.xml"
        for attr, value in (("address", "256"), ("address", "-1"), ("delay", "2147483648")):
            profile.write_text(f'<monitor name="Generic"><controls><control id="brightness" address="16" {attr}="{value}"/></controls></monitor>' if attr != "address" else f'<monitor name="Generic"><controls><control id="brightness" address="{value}"/></controls></monitor>')
            with self.assertRaises(Invalid):
                convert(self.source)
        profile.write_text('<monitor name="Generic"><controls><control id="input" address="16"><value id="wide" value="65536"/></control></controls></monitor>')
        with self.assertRaises(Invalid):
            convert(self.source)

    def test_unknown_optional_and_required_data_preserved(self):
        db = convert(self.source)
        db[1000] = {"future": b"\x00\xff"}
        db[6]["TST0001"][3] = [{0: "https://example.org/matcher/1", 1: True, 2: {0: 99}}]
        db[6]["VESA"][1001] = "optional inert data"
        self.assertEqual(load(encode(db)), db)
        source = Path(self.temp.name) / "future.cbor"
        output = Path(self.temp.name) / "rewritten.cbor"
        source.write_bytes(encode(db))
        subprocess.run([sys.executable, str(REPO / "scripts/cbor-db.py"), "rewrite", str(source), str(output)], check=True)
        self.assertEqual(source.read_bytes(), output.read_bytes())

    def test_required_extensions_guard_missing_cbor_fallback(self):
        safe = load((FIXTURES / "base-v1.cbor").read_bytes())
        future = load((FIXTURES / "descriptions-v1.cbor").read_bytes())
        self.assertEqual(fallback_manifest(safe), safe[8])
        self.assertIs(fallback_manifest(future), False)
        self.assertEqual(encode(fallback_manifest(future)), b"\xf4")
        output = Path(self.temp.name) / "future.cbor"
        snapshot = Path(self.temp.name) / "future.snapshot"
        subprocess.run([sys.executable, str(REPO / "scripts/cbor-db.py"), "rewrite",
                        str(FIXTURES / "descriptions-v1.cbor"), str(output),
                        "--snapshot", str(snapshot)], check=True)
        self.assertEqual(snapshot.read_bytes(), b"\xf4")
        self.assertEqual(output.read_bytes(), (FIXTURES / "descriptions-v1.cbor").read_bytes())

    def test_unknown_node_kinds_guard_missing_cbor_fallback(self):
        base = load((FIXTURES / "base-v1.cbor").read_bytes())
        for kind in (9, 254, 256, 2**64 - 1):
            for scope in ("options", "profile", "control"):
                db = copy.deepcopy(base)
                target = {"options": db[5], "profile": db[6]["TST0001"],
                          "control": db[6]["VESA"][2][0][2][0]}[scope]
                target[2].append({0: kind, 1: {}, 2: []})
                with self.subTest(kind=kind, scope=scope):
                    self.assertEqual(load(encode(db)), db)
                    self.assertIs(fallback_manifest(db), False)
        source = Path(self.temp.name) / "unknown-node.cbor"
        output = Path(self.temp.name) / "rewritten.cbor"
        snapshot = Path(self.temp.name) / "rewritten.snapshot"
        source.write_bytes(encode(db))
        subprocess.run([sys.executable, str(REPO / "scripts/cbor-db.py"), "rewrite",
                        str(source), str(output), "--snapshot", str(snapshot)], check=True)
        self.assertEqual(output.read_bytes(), source.read_bytes())
        self.assertEqual(snapshot.read_bytes(), b"\xf4")

    def test_inert_nodes_and_payloads_keep_xml_fallback(self):
        db = load((FIXTURES / "base-v1.cbor").read_bytes())
        db[6]["TST0001"][2].append({0: 255, 1: {}, 2: [],
            3: [{0: METADATA, 1: False, 2: {0: {}, 1: "inert-source"}}]})
        db[7] = [{0: "urn:example:description", 1: False, 2: {0: 9, 1: {}, 2: []}}]
        db[100] = {0: 256, 1: {}, 2: []}
        self.assertEqual(load(encode(db)), db)
        self.assertEqual(fallback_manifest(db), db[8])

    def test_snapshot_integrity(self):
        db = convert(self.source)
        db[8]["options.xml"] = bytes(32)
        with self.assertRaises(Invalid):
            validate(db)
        db = convert(self.source)
        db[8]["../escape"] = db[8].pop("options.xml")
        db[9] = hashlib.sha256(encode(db[8])).digest()
        with self.assertRaises(Invalid):
            validate(db)

    def test_failed_generation_removes_stale_artifacts(self):
        output = Path(self.temp.name) / "out.cbor"
        snapshot = Path(self.temp.name) / "out.snapshot"
        output.write_bytes(b"old")
        snapshot.write_bytes(b"old")
        (self.source / "monitor/VESA.xml").write_text("<broken")
        result = subprocess.run([sys.executable, str(REPO / "scripts/cbor-db.py"), "convert",
                                 str(self.source), str(output), "--snapshot", str(snapshot)], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output.exists())
        self.assertFalse(snapshot.exists())


if __name__ == "__main__":
    unittest.main()
