# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import sys

from pytoolbox import module

_all = module.All(globals())

if sys.version_info[0] > 2:
    from ipaddress import ip_address
else:
    try:
        from ipaddr import IP as ip_address
    except ImportError:  # previously IPAddress ...
        from ipaddr import IPAddress as ip_address

__all__ = ('ip_address', 'IPSocket')


def IPSocket(string):
    """
    This helper create a dictionary containing address and port from a parsed IP address string.
    Throws ValueError in case of failure (e.g. string is not a valid IP address).

    **Example usage**

    >>> IPSocket('gaga:gogo')
    Traceback (most recent call last):
        ...
    ValueError: gaga:gogo is not a valid IP socket.
    >>>
    >>> from pytoolbox.unittest import asserts
    >>> asserts.dict_equal(IPSocket('239.232.0.222:5004'), {
    ...     'ip': '239.232.0.222', 'port': 5004
    ... })

    .. warning::

        TODO IPv6 ready : >>> IPSocket('[2001:0db8:0000:0000:0000:ff00:0042]:8329')
    """
    try:
        (ip, port) = string.rsplit(':', 1)
        # ip = ip.translate(None, '[]')
        ip_address(ip)  # Seem not IPv6 ready
        port = int(port)
    except Exception:
        raise ValueError('{0} is not a valid IP socket.'.format(string))
    return {'ip': ip, 'port': port}


__all__ = _all.diff(globals())
