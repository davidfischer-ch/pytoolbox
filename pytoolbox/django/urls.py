# -*- encoding: utf-8 -*-

"""
Some utilities related to the URLs.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox import module
from pytoolbox.encoding import string_types
from pytoolbox.regex import UUID_REGEX

_all = module.All(globals())

INT_PK = r'(?P<pk>\d+)'
UUID_PK = r'(?P<pk>%s)' % UUID_REGEX


def get_named_patterns():
    """Returns a generator containing (pattern name, pattern) tuples."""
    from django.core.urlresolvers import get_resolver
    return (
        (k, v[0][0][0])
        for k, v in get_resolver(None).reverse_dict.iteritems()
        if isinstance(k, string_types)
    )


__all__ = _all.diff(globals())
