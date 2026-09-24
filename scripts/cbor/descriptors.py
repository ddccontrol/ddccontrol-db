"""Typed validation of the descriptive extension; never executes operations."""
import re

from codec import Invalid

IDENTITY = "https://ddccontrol.sourceforge.net/cbor/ext/function-description/1"


def _text(value):
    if not isinstance(value, str):
        raise Invalid("descriptor text has wrong type")


def identity(value):
    """Match the reader's identity grammar for envelopes and named contracts."""
    if (not isinstance(value, str)
            or not re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", value)
            or any(char.isspace() or ord(char) < 0x20 or 0x7f <= ord(char) <= 0x9f
                   for char in value)):
        raise Invalid("identity must be an absolute URI without whitespace or control characters")


def _bytes(value):
    if not isinstance(value, bytes):
        raise Invalid("descriptor binary data must be a byte string")


def _int(value):
    if type(value) is not int:
        raise Invalid("descriptor integer has wrong type")


def _range(low, high):
    def check(value):
        _int(value)
        if not low <= value <= high:
            raise Invalid("descriptor integer outside declared range")
    return check


_uint = _range(0, 2**64 - 1)
_vcp = _range(0, 255)


def _array(check):
    def array(value):
        if not isinstance(value, list):
            raise Invalid("descriptor collection must be an array")
        for item in value:
            check(item)
    return array


def _map(value, fields, required=(), extensible=False):
    if not isinstance(value, dict) or any(type(key) is not int or key < 0 for key in value):
        raise Invalid("descriptor map needs unsigned field IDs")
    if not set(required) <= value.keys():
        raise Invalid("missing required descriptor fields")
    if not extensible and not value.keys() <= fields.keys():
        raise Invalid("unassigned field in a fixed descriptor value")
    for key, check in fields.items():
        if key in value:
            check(value[key])


def _datum(value):
    if type(value) in (int, str, bytes):
        return
    _map(value, {0: _int, 1: _range(1, 2**64 - 1)}, required=(0, 1))


def _quantity(value):
    _map(value, {0: _range(1, 2), 1: _datum}, required=(0,))
    if (value[0] == 1) != (1 in value):
        raise Invalid("declared quantity requires datum; discovered quantity forbids datum")


def _choice(value):
    _map(value, {0: _datum, 1: _text}, required=(0,))


def _bitfield(value):
    _map(value, {0: _uint, 1: _range(1, 64), 2: _array(_choice), 3: _text}, required=(0, 1))


def _version(value):
    _map(value, {0: identity, 1: _text}, required=(0, 1))


def _condition(value):
    _map(value, {0: identity, 1: lambda _: None}, required=(0, 1))


def _opaque(value):
    _map(value, {0: identity, 1: identity, 2: _bytes}, required=(0, 1, 2))


def _operation(value):
    _map(value, {0: _uint, 1: _vcp, 2: lambda _: None, 3: identity,
                 4: _array(_condition)}, required=(0,), extensible=True)


def validate(value, extensions):
    """Check payload types; necessity and hardware support are caller concerns."""
    _map(value, {0: _range(1, 6), 1: _range(0, 3), 2: _array(_operation),
                 3: identity, 4: _vcp, 5: identity, 6: _quantity, 7: _quantity,
                 8: _quantity, 9: _quantity, 10: _array(_choice),
                 11: _array(_bitfield), 12: _array(_version), 13: _text,
                 14: _array(_vcp), 15: _array(_condition), 16: _array(_opaque),
                 17: _text, 18: extensions, 19: _array(_condition)}, extensible=True)
