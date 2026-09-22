"""Restricted RFC 8949 section 4.2.1 deterministic CBOR reference codec.

Deliberately independent of Rust's decoder. Never use this module for a more
permissive general CBOR protocol. Maps are checked before insertion.
"""

MAX_FILE = 256 * 1024 * 1024
MAX_DEPTH = 64
MAX_ITEMS = 4_000_000
MAX_CONTAINER = 1_000_000
MAX_TEXT = 1024 * 1024
MAX_BYTES = 16 * 1024 * 1024


class Invalid(ValueError):
    """Invalid data or data outside the format's normative resource bounds."""


def _head(major, value):
    if not 0 <= value <= 0xffffffffffffffff:
        raise Invalid("integer exceeds CBOR's 64-bit argument range")
    lead = major << 5
    if value < 24:
        return bytes([lead | value])
    for width, extra in [(1, 24), (2, 25), (4, 26), (8, 27)]:
        if value < 1 << (width * 8):
            return bytes([lead | extra]) + value.to_bytes(width, "big")
    raise AssertionError("unreachable integer width")


def encode(value):
    """Encode and validate one deterministic CBOR value."""
    def item(value, depth):
        if depth > MAX_DEPTH:
            raise Invalid("nesting exceeds 64")
        if value is None:
            return b"\xf6"
        if value is False:
            return b"\xf4"
        if value is True:
            return b"\xf5"
        if isinstance(value, int):
            return _head(0 if value >= 0 else 1, value if value >= 0 else -1 - value)
        if isinstance(value, (bytes, str)):
            payload = value if isinstance(value, bytes) else value.encode("utf-8")
            limit = MAX_BYTES if isinstance(value, bytes) else MAX_TEXT
            if len(payload) > limit:
                raise Invalid("string exceeds normative length")
            return _head(2 if isinstance(value, bytes) else 3, len(payload)) + payload
        if isinstance(value, (list, dict)):
            if len(value) > MAX_CONTAINER:
                raise Invalid("container exceeds normative length")
            if isinstance(value, list):
                return _head(4, len(value)) + b"".join(item(v, depth + 1) for v in value)
            entries = []
            for key, val in value.items():
                if type(key) not in (int, str) or (type(key) is int and key < 0):
                    raise Invalid("map key must be unsigned integer or text")
                entries.append((item(key, depth + 1), item(val, depth + 1)))
            entries.sort(key=lambda entry: entry[0])
            return _head(5, len(entries)) + b"".join(k + v for k, v in entries)
        raise Invalid("unsupported CBOR value type: " + type(value).__name__)

    data = item(value, 0)
    # Keep all parser bounds identical for writing and reading, including the
    # aggregate item count. A producer must not emit an unreadable database.
    decode(data)
    return data


def decode(data):
    """Decode exactly one value, rejecting non-deterministic wire encodings."""
    if len(data) > MAX_FILE:
        raise Invalid("file exceeds 256 MiB")
    offset = 0
    items = 0

    def take(length):
        nonlocal offset
        if length > len(data) - offset:
            raise Invalid("truncated CBOR")
        value = data[offset:offset + length]
        offset += length
        return value

    def item(depth):
        nonlocal offset, items
        if depth > MAX_DEPTH:
            raise Invalid("nesting exceeds 64")
        items += 1
        if items > MAX_ITEMS:
            raise Invalid("aggregate item limit exceeded")
        initial = take(1)[0]
        major, extra = initial >> 5, initial & 31
        if major == 7:
            if extra == 20:
                return False
            if extra == 21:
                return True
            if extra == 22:
                return None
            raise Invalid("floating point and unassigned simple values forbidden")
        if major == 6:
            raise Invalid("CBOR tags forbidden")
        if extra < 24:
            arg = extra
        elif extra <= 27:
            width = 1 << (extra - 24)
            arg = int.from_bytes(take(width), "big")
            minimum = {1: 24, 2: 256, 4: 65536, 8: 4294967296}[width]
            if arg < minimum:
                raise Invalid("non-shortest integer or length")
        else:
            raise Invalid("indefinite lengths and reserved additional information forbidden")
        if major == 0:
            return arg
        if major == 1:
            return -1 - arg
        if major in (2, 3):
            if arg > (MAX_BYTES if major == 2 else MAX_TEXT):
                raise Invalid("string exceeds normative length")
            value = take(arg)
            if major == 2:
                return value
            try:
                return value.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise Invalid("invalid UTF-8") from exc
        if arg > MAX_CONTAINER:
            raise Invalid("container exceeds normative length")
        # Each member requires at least one byte. Reject impossible allocation
        # claims without allocating arrays or waiting for their contents.
        needed = arg * (2 if major == 5 else 1)
        if needed > len(data) - offset:
            raise Invalid("container length exceeds remaining input")
        if major == 4:
            return [item(depth + 1) for _ in range(arg)]
        if major == 5:
            value = {}
            previous = None
            for _ in range(arg):
                start = offset
                key = item(depth + 1)
                raw = data[start:offset]
                if type(key) not in (int, str) or (type(key) is int and key < 0):
                    raise Invalid("map key must be unsigned integer or text")
                if key in value:
                    raise Invalid("duplicate map key")
                if previous is not None and raw <= previous:
                    raise Invalid("map keys not in bytewise deterministic order")
                previous = raw
                value[key] = item(depth + 1)
            return value
        raise Invalid("invalid major type")

    value = item(0)
    if offset != len(data):
        raise Invalid("trailing data after root value")
    return value


def diagnostic(value):
    """Lossless JSON-friendly form; maps and bytes are always explicitly tagged."""
    if isinstance(value, bytes):
        return {"$bytes": value.hex()}
    if isinstance(value, dict):
        return {"$map": [[diagnostic(k), diagnostic(v)] for k, v in value.items()]}
    if isinstance(value, list):
        return [diagnostic(v) for v in value]
    return value
