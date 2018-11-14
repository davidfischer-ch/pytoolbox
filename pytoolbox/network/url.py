# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from urlparse import urlsplit, urlunsplit

from pytoolbox import string


def with_subdomain(url, subdomain=None):
    """
    Return the ``url`` with the sub-domain replaced with ``subdomain``.

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> eq = asserts.equal
    >>> asserts.equal(
    ...     with_subdomain('http://app.website.com/page'),
    ...     'http://website.com/page')
    >>> asserts.equal(
    ...     with_subdomain('http://app.website.com/page', 'help'),
    ...     'http://help.website.com/page')
    >>> asserts.equal(
    ...     with_subdomain('https://app.website.com#d?page=1', 'help'),
    ...     'https://help.website.com#d?page=1')
    """
    import tldextract
    components = list(urlsplit(url))
    components[1] = string.filterjoin((subdomain, ) + tldextract.extract(components[1])[1:], '.')
    return urlunsplit(components)
