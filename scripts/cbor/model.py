"""The explicit candidate-v1 field register and XML source conversion."""
import hashlib
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from codec import Invalid, MAX_FILE, decode, encode
import descriptors

MAGIC = b"DDCDB"
METADATA = "https://ddccontrol.sourceforge.net/cbor/ext/source-metadata/1"
KINDS = {"options": 0, "group": 1, "subgroup": 2, "control": 3,
         "value": 4, "monitor": 5, "caps": 6, "include": 7, "controls": 8}
ATTRS = {"name": 0, "id": 1, "type": 2, "refresh": 3, "pattern": 4,
         "init": 5, "address": 6, "delay": 7, "value": 8, "file": 9,
         "add": 10, "remove": 11, "dbversion": 12, "date": 13,
         "caps": 14, "include": 15}
CONTEXT = {"options": {"dbversion", "date"}, "group": {"name"},
           "subgroup": {"name", "pattern"}, "option-control": {"id", "name", "type", "refresh"},
           "option-value": {"id", "name"}, "monitor": {"name", "init", "caps", "include"},
           "monitor-control": {"id", "address", "delay"}, "monitor-value": {"id", "value"},
           "caps": {"add", "remove"}, "include": {"file"}, "controls": set()}
CONTEXT_ROLES = {
    ("options", "", "options"): "options",
    ("group", "options", "options"): "group",
    ("subgroup", "group", "options"): "subgroup",
    ("control", "subgroup", "options"): "option-control",
    ("value", "control", "options"): "option-value",
    ("monitor", "", "monitor"): "monitor",
    ("control", "controls", "monitor"): "monitor-control",
    ("value", "control", "monitor"): "monitor-value",
    ("caps", "monitor", "monitor"): "caps",
    ("include", "monitor", "monitor"): "include",
}


def executable_attributes(tag, parent, root):
    return CONTEXT.get(CONTEXT_ROLES.get((tag, parent, root)), set())


def executable_path(tag, parent, root, ancestor_active):
    return ancestor_active and ((tag, parent, root) in CONTEXT_ROLES
                                or (tag, parent, root) == ("controls", "monitor", "monitor"))


def local_name(tag):
    # roxmltree dispatches element names using their local name, regardless of
    # namespace. Attributes remain active only when they are unqualified.
    return tag.rsplit("}", 1)[-1] if tag.startswith("{") else tag


PROFILE_ID = re.compile(r"[A-Za-z0-9_-]{1,255}\Z")
MAX_PROFILES = 65536
MAX_INCLUDE_DEPTH = 256
MAX_INCLUDE_VISITS = 1_000_000


def integer(raw, attribute):
    # Match Rust's legacy strtol-style base-0 grammar exactly. Leading ASCII
    # whitespace and a sign are accepted; trailing whitespace is not. Delay
    # alone is decimal, so leading zeroes never make a delay octal.
    text = raw.lstrip(" \t\n\r\v\f")
    sign = -1 if text.startswith("-") else 1
    digits = text[1:] if text.startswith(("-", "+")) else text
    radix = 10
    if attribute != "delay":
        if digits.startswith(("0x", "0X")):
            radix, digits = 16, digits[2:]
        elif len(digits) > 1 and digits.startswith("0"):
            radix, digits = 8, digits[1:]
    pattern = {8: r"[0-7]+", 10: r"[0-9]+", 16: r"[0-9A-Fa-f]+"}[radix]
    if not re.fullmatch(pattern, digits):
        raise Invalid("invalid integer for " + attribute + ": " + repr(raw))
    lo, hi = {"address": (0, 255), "value": (0, 65535),
              "delay": (-2147483648, 2147483647), "dbversion": (3, 3)}[attribute]
    # Accumulate within the field's bound instead of constructing an unbounded
    # Python integer. Long leading-zero literals stay portable across Python's
    # configurable decimal-string limits; overflow gets the normal diagnostic.
    value = 0
    for digit in digits.lstrip("0"):
        value = value * radix + int(digit, radix)
        if value > max(abs(lo), abs(hi)):
            raise Invalid(attribute + " outside normative range")
    value *= sign
    if not lo <= value <= hi:
        raise Invalid(attribute + " outside normative range")
    return value


def parse_xml(data, expected):
    # Match the reader's supported legacy normalization and its WHATWG
    # ISO-8859-1/ASCII aliases (Windows-1252, not Python's Latin-1 codec).
    # Unimplemented labels are explicitly rejected instead of guessing.
    def declaration_start(value):
        cursor = 0
        while True:
            while cursor < len(value) and value[cursor:cursor + 1] in b" \t\r\n\v\f":
                cursor += 1
            if not value[cursor:].startswith(b"<!--"):
                return cursor if value[cursor:].startswith(b"<?xml") else None
            end = value.find(b"-->", cursor + 4)
            if end < 0:
                return None
            cursor = end + 3

    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        decoded = data.decode("utf-16")
    else:
        start = declaration_start(data)
        declaration = data[start:start + 256].split(b"?>")[0] if start is not None else b""
        match = re.search(br"encoding\s*=\s*['\"]([^'\"]+)['\"]", declaration)
        label = match[1].decode("ascii").lower() if match else "utf-8"
        if label in {"utf-8", "utf8", "unicode-1-1-utf-8"}:
            encoding = "utf-8-sig"
        elif label in {"windows-1252", "cp1252", "iso-8859-1", "iso8859-1",
                       "iso_8859-1", "latin1", "latin-1", "l1", "ascii", "us-ascii"}:
            encoding = "cp1252"
        else:
            raise Invalid("unsupported source XML encoding: " + label)
        decoded = data.decode(encoding)
    cursor = 0
    while True:
        cursor += len(decoded[cursor:]) - len(decoded[cursor:].lstrip())
        if not decoded[cursor:].startswith("<!--"):
            break
        end = decoded.find("-->", cursor + 4)
        if end < 0:
            break
        cursor = end + 3
    if cursor and decoded[cursor:].startswith("<?xml"):
        decoded = decoded[cursor:]
    if "<!DOCTYPE" in decoded.upper() or "<!ENTITY" in decoded.upper():
        raise Invalid("DTDs and entity declarations are not database source")
    class NoDoctype(ET.TreeBuilder):
        def doctype(self, name, pubid, system):
            raise Invalid("DTDs and entity declarations are not database source")

    try:
        root = ET.fromstring(decoded, parser=ET.XMLParser(target=NoDoctype()))
    except (ET.ParseError, ValueError) as exc:
        raise Invalid(str(exc)) from exc
    if local_name(root.tag) != expected:
        raise Invalid("expected XML root " + expected)

    def node(element, parent="", depth=0, ancestor_active=True):
        if depth > 64:
            raise Invalid("XML element nesting exceeds conversion resource bound")
        tag = local_name(element.tag)
        path_active = executable_path(tag, parent, expected, ancestor_active)
        allowed = executable_attributes(tag, parent, expected) if path_active else set()
        active = {}
        inert = {}
        for name, value in element.attrib.items():
            if name in allowed:
                active[ATTRS[name]] = integer(value, name) if name in ("address", "delay", "value", "dbversion") else value
            else:
                inert[name] = value
        result = {0: KINDS.get(tag, 255), 1: active, 2: [node(c, tag, depth + 1, path_active) for c in element]}
        metadata = {}
        if inert:
            metadata[0] = inert
        if tag not in KINDS:
            metadata[1] = tag
        if element.text and element.text.strip():
            metadata[2] = element.text
        if element.tail and element.tail.strip():
            metadata[3] = element.tail
        if metadata:
            metadata.setdefault(0, {})
            result[3] = [{0: METADATA, 1: False, 2: metadata}]
        return result

    return node(root)


def source_files(directory):
    directory = Path(directory)
    paths = [directory / "options.xml", *sorted((directory / "monitor").glob("*.xml"))]
    if len(paths) == 1:
        raise Invalid("database has no monitor profiles")
    sources = {}
    size = 0
    for path in paths:
        with path.open("rb") as stream:
            data = stream.read(MAX_FILE + 1)
        size += len(data)
        if size > MAX_FILE:
            raise Invalid("XML source snapshot exceeds 256 MiB conversion resource limit")
        sources[path.relative_to(directory).as_posix()] = data
    return sources


def convert(directory, revision=None):
    sources = source_files(directory)
    try:
        options = parse_xml(sources["options.xml"], "options")
    except Invalid as exc:
        raise Invalid("options.xml: " + str(exc)) from exc
    revision = revision if revision is not None else options[1].get(13)
    if not revision:
        raise Invalid("database revision is required")
    profiles = {}
    for path, data in sources.items():
        if path == "options.xml":
            continue
        identifier = path[len("monitor/"):-4]
        if not PROFILE_ID.fullmatch(identifier) or identifier in (".", ".."):
            raise Invalid("unsafe profile identifier: " + identifier)
        try:
            profiles[identifier] = parse_xml(data, "monitor")
        except Invalid as exc:
            raise Invalid(path + ": " + str(exc)) from exc
    manifest = {path: hashlib.sha256(data).digest() for path, data in sources.items()}
    db = {0: MAGIC, 1: 1, 2: revision, 3: 3, 4: "ddccontrol-db", 5: options,
          6: profiles, 8: manifest, 9: hashlib.sha256(encode(manifest)).digest()}
    validate(db)
    # Detect additions, deletions and replacements during source collection.
    if sources != source_files(directory):
        raise Invalid("XML source snapshot changed during generation")
    return db


def _map(value, label):
    if not isinstance(value, dict):
        raise Invalid(label + " must be a map")


def _uint_map(value, label):
    _map(value, label)
    if any(type(k) is not int or k < 0 for k in value):
        raise Invalid(label + " keys must be unsigned integers")


def extensions(value):
    if not isinstance(value, list):
        raise Invalid("extensions must be an array")
    identities = set()
    for ext in value:
        _uint_map(ext, "extension")
        if not {0, 1, 2} <= ext.keys():
            raise Invalid("extension fields 0/1/2 required")
        descriptors.identity(ext[0])
        if type(ext[1]) is not bool:
            raise Invalid("extension necessity must be boolean")
        if ext[0] in identities:
            raise Invalid("duplicate extension identity")
        identities.add(ext[0])
        if ext[0] == descriptors.IDENTITY:
            descriptors.validate(ext[2], extensions)
        if ext[0] == METADATA:
            if ext[1]:
                raise Invalid("source metadata must be optional")
            payload = ext[2]
            _uint_map(payload, "source metadata")
            if 0 not in payload:
                raise Invalid("source metadata requires ignored-attribute map")
            _map(payload[0], "ignored attributes")
            if any(not isinstance(k, str) or not isinstance(v, str) for k, v in payload[0].items()):
                raise Invalid("ignored attributes must map text to text")
            if any(k in payload and not isinstance(payload[k], str) for k in (1, 2, 3)):
                raise Invalid("source tag/text/tail must be text")


def validate(db):
    """Validate structural contract; unknown required features remain representable.

    A consumer additionally negotiates required features before using a unit.
    This validator must permit new required identities so it can generate them.
    """
    _uint_map(db, "database")
    if not set(range(7)) | {8, 9} <= db.keys():
        raise Invalid("missing required database fields")
    if db[0] != MAGIC or type(db[1]) is not int or db[1] != 1:
        raise Invalid("unsupported database identification or format version")
    if type(db[3]) is not int or db[3] != 3 or db[4] != "ddccontrol-db":
        raise Invalid("unsupported XML semantic contract or gettext domain")
    if not isinstance(db[2], str) or not db[2]:
        raise Invalid("revision must be nonempty text")
    extensions(db.get(7, []))
    _map(db[6], "profiles")
    if not 1 <= len(db[6]) <= MAX_PROFILES:
        raise Invalid("profile count outside bounds")
    refs = {key: [] for key in db[6]}

    def node(n, expected_root=None, ref_list=None, depth=0, parent="", root="options", ancestor_active=True):
        if depth > 64:
            raise Invalid("node nesting exceeds CBOR bound")
        _uint_map(n, "node")
        if not {0, 1, 2} <= n.keys():
            raise Invalid("node fields 0/1/2 required")
        if type(n[0]) is not int or n[0] < 0:
            raise Invalid("node kind must be unsigned integer")
        if expected_root is not None and n[0] != expected_root:
            raise Invalid("invalid root node kind")
        _uint_map(n[1], "attributes")
        tag = next((name for name, kind in KINDS.items() if kind == n[0]), "unknown")
        path_active = executable_path(tag, parent, root, ancestor_active)
        allowed = {ATTRS[name] for name in executable_attributes(tag, parent, root)} if path_active else set()
        for key, value in n[1].items():
            if key < 16 and key not in allowed:
                raise Invalid("attribute is not executable in its node context")
            if key < 16 and isinstance(value, str) and "\0" in value:
                raise Invalid("NUL forbidden in executable text")
            if key in (6, 7, 8, 12):
                if type(value) is not int:
                    raise Invalid("numeric attribute is not integer")
                lo, hi = {6: (0, 255), 7: (-2147483648, 2147483647), 8: (0, 65535), 12: (3, 3)}[key]
                if not lo <= value <= hi:
                    raise Invalid("numeric attribute outside range")
            elif key <= 15 and not isinstance(value, str):
                raise Invalid("text attribute has wrong type")
            elif key >= 16 and type(value) not in (int, str):
                raise Invalid("unknown attributes must be integer or text")
        if not isinstance(n[2], list):
            raise Invalid("children must be array")
        extensions(n.get(3, []))
        if n[0] == 255 and not any(e[0] == METADATA and e[1] is False and isinstance(e[2], dict) and isinstance(e[2].get(1), str) for e in n.get(3, [])):
            raise Invalid("inert unknown node requires original-tag metadata")
        if n[0] == 255 and any(e[0] == METADATA and e[2].get(1) in KINDS for e in n.get(3, [])):
            raise Invalid("inert source node cannot impersonate known element")
        if ref_list is not None and n[0] == 7 and path_active:
            target = n[1].get(9)
            if not isinstance(target, str) or target not in refs:
                raise Invalid("missing include target: " + str(target))
            ref_list.append(target)
        for child in n[2]:
            node(child, ref_list=ref_list if path_active else None, depth=depth + 1, parent=tag, root=root, ancestor_active=path_active)

    node(db[5], 0)
    for identifier, profile in db[6].items():
        if not isinstance(identifier, str) or not PROFILE_ID.fullmatch(identifier) or identifier in (".", ".."):
            raise Invalid("invalid profile identifier")
        node(profile, 5, refs[identifier], root="monitor")
    memo = {}

    def graph(identifier, stack=()):
        if identifier in stack:
            raise Invalid("include cycle: " + " -> ".join(stack + (identifier,)))
        if len(stack) >= MAX_INCLUDE_DEPTH:
            raise Invalid("include depth exceeds 256")
        if identifier in memo:
            return memo[identifier]
        height, visits = 1, 1
        for target in refs[identifier]:
            h, v = graph(target, stack + (identifier,))
            height = max(height, h + 1)
            visits += v
            if visits > MAX_INCLUDE_VISITS:
                raise Invalid("expanded include visits exceed 1000000")
        if height > MAX_INCLUDE_DEPTH:
            raise Invalid("include depth exceeds 256")
        memo[identifier] = height, visits
        return height, visits

    for identifier in refs:
        graph(identifier)
    _map(db[8], "source manifest")
    expected_paths = {"options.xml"} | {"monitor/" + key + ".xml" for key in db[6]}
    if set(db[8]) != expected_paths:
        raise Invalid("manifest paths do not match complete profile inventory")
    for path, digest in db[8].items():
        if not isinstance(path, str) or not isinstance(digest, bytes) or len(digest) != 32:
            raise Invalid("invalid source manifest entry")
    if not isinstance(db[9], bytes) or db[9] != hashlib.sha256(encode(db[8])).digest():
        raise Invalid("snapshot does not match source manifest")
    return db


def load(data):
    return validate(decode(data))


def fallback_manifest(database):
    """Return a snapshot manifest or permanent false guard for XML fallback.

    New dual bundles must always install this sidecar. Unknown necessary
    semantics cannot be discarded simply by deleting the CBOR file. This is
    deliberately conservative for nested future extension envelopes too.
    """
    known_kinds = set(KINDS.values()) | {255}

    def unknown_kind(node):
        # New node kinds are necessary syntax even without an envelope. Check
        # actual node trees only: node-shaped opaque payloads remain inert.
        return node[0] not in known_kinds or any(unknown_kind(child) for child in node[2])

    def necessary(value):
        if isinstance(value, dict):
            if (isinstance(value.get(0), str) and value.get(1) is True
                    and 2 in value and re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", value[0])):
                return True
            return any(necessary(item) for item in value.values())
        return isinstance(value, list) and any(necessary(item) for item in value)

    if (unknown_kind(database[5]) or any(unknown_kind(node) for node in database[6].values())
            or necessary(database)):
        return False
    return database[8]
