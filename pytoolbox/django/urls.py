"""
Some utilities related to the URLs.
"""
from __future__ import annotations

try:
    from django.urls import get_resolver
except ImportError:
    # For Django < 2.0
    from django.core.urlresolvers import get_resolver

from pytoolbox.regex import UUID_REGEX

__all__ = ['INT_PK', 'UUID_PK', 'get_named_patterns']

INT_PK = r'(?P<pk>\d+)'
UUID_PK = r'(?P<pk>%s)' % UUID_REGEX


def get_named_patterns():
    """Returns a generator containing (pattern name, pattern) tuples."""
    return (
        (k, v[0][0][0])
        for k, v in get_resolver(None).reverse_dict.items()
        if isinstance(k, str)
    )
