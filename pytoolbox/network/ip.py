from __future__ import annotations

from ipaddress import ip_address

from pytoolbox import exceptions

__all__ = ['ip_address', 'IPSocket']


def IPSocket(socket):  # pylint:disable=invalid-name
    """
    This helper create a dictionary containing address and port from a parsed IP address string.
    Throws InvalidIPSocketError in case of failure.

    **Example usage**

    >>> IPSocket('gaga:gogo')
    Traceback (most recent call last):
        ...
    pytoolbox.exceptions.InvalidIPSocketError: gaga:gogo is not a valid IP socket.
    >>>
    >>> from pytoolbox.unittest import asserts
    >>> asserts.dict_equal(
    ...     IPSocket('239.232.0.222:5004'),
    ...     {'ip': '239.232.0.222', 'port': 5004})

    .. warning::

        TODO IPv6 ready : >>> IPSocket('[2001:0db8:0000:0000:0000:ff00:0042]:8329')
    """
    try:
        (address, port) = socket.rsplit(':', 1)
        # address = address.translate(None, '[]')
        ip_address(address)  # Seem not IPv6 ready
        port = int(port)
    except Exception as ex:
        raise exceptions.InvalidIPSocketError(socket=socket) from ex
    return {'ip': address, 'port': port}
