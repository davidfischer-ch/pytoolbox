from ipaddress import ip_address

__all__ = ['ip_address', 'IPSocket']


def IPSocket(string):  # pylint:disable=invalid-name
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
    >>> asserts.dict_equal(
    ...     IPSocket('239.232.0.222:5004'),
    ...     {'ip': '239.232.0.222', 'port': 5004})

    .. warning::

        TODO IPv6 ready : >>> IPSocket('[2001:0db8:0000:0000:0000:ff00:0042]:8329')
    """
    try:
        (address, port) = string.rsplit(':', 1)
        # address = address.translate(None, '[]')
        ip_address(address)  # Seem not IPv6 ready
        port = int(port)
    except Exception:
        raise ValueError(f'{string} is not a valid IP socket.')
    return {'ip': address, 'port': port}
