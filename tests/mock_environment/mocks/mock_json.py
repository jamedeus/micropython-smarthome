import json
from math import isnan


# Takes list or dict, returns True if any items are NaN, otherwise returns False
def contains_nan(test):
    if isinstance(test, dict):
        # Check keys and values
        for k, v in test.items():
            if (isinstance(k, float) and isnan(k)) or (isinstance(v, float) and isnan(v)):
                return True
    elif isinstance(test, list):
        for i in test:
            if isinstance(i, float) and isnan(i):
                return True
    return False


# Subclass, catch JSONDecodeError, replace with OSError (match micropython behavior)
# Raise ValueError if decoded JSON contains NaN to match micropython behavior
class MockDecoder(json.JSONDecoder):
    def decode(self, s, *args):
        try:
            decoded = super().decode(s)
            if contains_nan(decoded):
                raise ValueError("syntax error in JSON")
            return decoded
        except json.JSONDecodeError:
            raise OSError


# Copied from source, JSONDecodeError replaced with OSError,
# JSONDecoder replaced with MockDecoder (above)
def mock_loads(s, *, cls=None, object_hook=None, parse_float=None,
        parse_int=None, parse_constant=None, object_pairs_hook=None, **kw):
    if isinstance(s, str):
        if s.startswith('\ufeff'):
            raise OSError("Unexpected UTF-8 BOM (decode using utf-8-sig)", s, 0)
    else:
        if not isinstance(s, (bytes, bytearray)):
            raise TypeError(f'the JSON object must be str, bytes or bytearray, '
                            f'not {s.__class__.__name__}')
        s = s.decode(json.detect_encoding(s), 'surrogatepass')

    if (cls is None and object_hook is None and
            parse_int is None and parse_float is None and
            parse_constant is None and object_pairs_hook is None and not kw):
        return MockDecoder(object_hook=None, object_pairs_hook=None).decode(s)
    if cls is None:
        cls = MockDecoder
    if object_hook is not None:
        kw['object_hook'] = object_hook
    if object_pairs_hook is not None:
        kw['object_pairs_hook'] = object_pairs_hook
    if parse_float is not None:
        kw['parse_float'] = parse_float
    if parse_int is not None:
        kw['parse_int'] = parse_int
    if parse_constant is not None:
        kw['parse_constant'] = parse_constant
    return cls(**kw).decode(s)
