"""
Some utilities related to the URLs.
"""

from __future__ import annotations

try:
    from django.urls import get_resolver
except ImportError:
    # For Django < 2.0
    from django.core.urlresolvers import get_resolver

from collections.abc import Generator
from typing import Final

from pytoolbox.regex import UUID_REGEX

__all__ = ['INT_PK', 'UUID_PK', 'get_named_patterns']

INT_PK: Final[str] = r'(?P<pk>\d+)'
UUID_PK: Final[str] = f'(?P<pk>{UUID_REGEX})'


def get_named_patterns() -> Generator[tuple[str, str]]:
    """Return a generator containing (pattern name, pattern) tuples."""
    return (
        (k, v[0][0][0]) for k, v in get_resolver(None).reverse_dict.items() if isinstance(k, str)
    )
