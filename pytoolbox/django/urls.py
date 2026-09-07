"""
Some utilities related to the URLs.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Final

from django.urls import get_resolver

from pytoolbox.regex import UUID_REGEX

__all__ = ['INT_PK', 'UUID_PK', 'get_named_patterns']

INT_PK: Final[str] = r'(?P<pk>\d+)'
UUID_PK: Final[str] = f'(?P<pk>{UUID_REGEX})'


def get_named_patterns() -> Generator[tuple[str, str]]:
    """Return a generator containing (pattern name, pattern) tuples."""
    # Each entry is ((possibilities, pattern), ...); the first pattern is the canonical one.
    return (
        (name, entry[0][0][0])  # pyrefly: ignore[bad-index]
        for name, entry in get_resolver(None).reverse_dict.items()
        if isinstance(name, str)
    )
