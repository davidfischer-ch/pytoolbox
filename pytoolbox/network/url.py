from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

from pytoolbox import string

__all__ = ['with_subdomain']


def with_subdomain(url, subdomain=None):
    """
    Return the ``url`` with the sub-domain replaced with ``subdomain``.

    **Example usage**

    >>> sub = with_subdomain
    >>> assert sub('http://app.website.com/page') == 'http://website.com/page'
    >>> assert sub('http://some.app.website.com/page') == 'http://website.com/page'
    >>> assert sub('http://app.website.com/page', 'help') == 'http://help.website.com/page'
    >>> assert sub('https://app.website.com#d?page=1', 'help'), 'https://help.website.com#d?page=1'
    """
    import tldextract
    components = list(urlsplit(url))
    extracted = tldextract.extract(components[1])
    components[1] = string.filterjoin((subdomain, extracted.domain, extracted.suffix), '.')
    return urlunsplit(components)
