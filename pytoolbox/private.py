from __future__ import annotations

try:
    from bson.objectid import ObjectId  # pylint:disable=unused-import
    from bson.errors import InvalidId   # pylint:disable=unused-import
except ImportError:
    InvalidId = ObjectId = None


def _parse_kwargs_string(kwargs_string, **types):
    if not kwargs_string:
        return {}
    kwargs_list = [kwarg.strip().split('=') for kwarg in kwargs_string.split(';')]
    return {k: types[k](v) for k, v in kwargs_list}
