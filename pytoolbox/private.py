"""
Helpers shared across pytoolbox modules, and optional dependency imports (e.g. :mod:`bson`).
"""

from __future__ import annotations

from typing import Any

try:
    from bson.errors import InvalidId  # pylint:disable=unused-import
    from bson.objectid import ObjectId  # pylint:disable=unused-import
except ImportError:
    InvalidId = ObjectId = None  # type: ignore[assignment, misc]


def parse_kwargs_string(kwargs_string: str | None, **types: type[Any]) -> dict[str, Any]:
    """Return the ``;``-separated ``key=value`` pairs of *kwargs_string*, typed by *types*."""
    if not kwargs_string:
        return {}
    kwargs_list = [kwarg.strip().split('=') for kwarg in kwargs_string.split(';')]
    return {k: types[k](v) for k, v in kwargs_list}
