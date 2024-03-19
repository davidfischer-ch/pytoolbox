from __future__ import annotations

from typing import Any, get_type_hints
from urllib.parse import urlparse
import errno
import inspect
import http.client
import os
import re
import socket
import uuid

from . import module
from .network.ip import ip_address
from .private import InvalidId, ObjectId

_all = module.All(globals())


class CleanAttributesMixin(object):  # pylint:disable=too-few-public-methods
    """
    Put validation logic, cleanup code, ... into a method clean_<attribute_name> and this method
    will be called every time the attribute is set.

    **Example usage**

    >>> class Settings(CleanAttributesMixin):
    ...
    ...     def __init__(self, locale, broker):
    ...        self.locale = locale
    ...        self.broker = broker
    ...
    ...     def clean_locale(self, value):
    ...         value = str(value)
    ...         assert len(value) == 2
    ...         return value
    ...
    >>> settings = Settings('fr', {})
    >>> settings = Settings(10, {})
    >>> assert isinstance(settings.locale, str)
    >>> settings = Settings(100, 'a string')
    Traceback (most recent call last):
        ...
    AssertionError
    """
    def __setattr__(self, name: str, value: Any) -> None:
        if cleanup_method := getattr(self, 'clean_' + name, None):
            value = cleanup_method(value)
        super().__setattr__(name, value)


class StrongTypedMixin(object):  # pylint:disable=too-few-public-methods
    """
    Annotate arguments of the class __init__ with types and then you'll get a class with type
    checking.

    A more beefy alternative is pydantic.

    **Example usage**

    >>> class Settings(StrongTypedMixin):
    ...     def __init__(
    ...         self, *,
    ...         locale: str | list,
    ...         broker: dict | None = None,
    ...         debug: bool = True,
    ...         timezone: str | None = None
    ...     ) -> None:
    ...        self.locale = locale
    ...        self.broker = broker
    ...        self.debug = debug
    ...        self.timezone = timezone
    ...
    >>> settings = Settings(locale='fr', broker={}, debug=False)
    >>> settings = Settings(
    ...     locale='fr', broker={}, timezone='this argument is not type checked')
    >>> settings = Settings(locale='fr')
    >>> print(settings.broker)
    None
    >>> settings = Settings(locale=['en', 'fr'], broker={})
    >>> settings = Settings(locale=10, broker={})
    Traceback (most recent call last):
        ...
    ValueError: Attribute locale must be set to an instance of str | list
    """
    def __setattr__(self, name: str, value: Any) -> None:
        if the_type := get_type_hints(self.__init__).get(name):
            default = inspect.signature(self.__init__).parameters[name].default
            if value != default and not isinstance(value, the_type):
                raise ValueError(f'Attribute {name} must be set to an instance of {the_type}')
        super().__setattr__(name, value)


def valid_filename(name: str) -> bool:
    """
    Returns True if `name` is a valid file name.

    **Example usage**

    >>> valid_filename('my_file_without_extension')
    False
    >>> valid_filename('my_file_with_extension.mp4')
    True
    """
    try:
        return re.match(r'[^\.]+\.[^\.]+', name) is not None
    except Exception:  # pylint:disable=broad-except
        return False


def valid_ip(address: str) -> bool:
    """
    Returns True if `ip` is a valid IP address.

    **Example usage**

    >>> valid_ip('123.0.0.')
    False
    >>> valid_ip('239.232.0.222')
    True
    """
    try:
        ip_address(address)
        return True
    except Exception:  # pylint:disable=broad-except
        return False


def valid_email(email: str) -> bool:
    """
    Returns True if `email` is a valid e-mail address.

    **Example usage**

    >>> valid_email('Tabby@croquetes')
    False
    >>> valid_email('Tabby@bernex.ch')
    True
    """
    try:
        return re.match(r'[^@]+@[^@]+\.[^@]+', email) is not None
    except Exception:  # pylint:disable=broad-except
        return False


def valid_int(value: Any) -> bool:
    """
    Returns True if `value` is a valid integer (can be converted to an int).

    **Example usage**

    >>> valid_int('dimitri is not a valid integer')
    False
    >>> valid_int('-10')
    True
    """
    try:
        int(value)
        return True
    except ValueError:  # pylint:disable=broad-except
        return False


def valid_port(port: int | str) -> bool:
    """
    Returns True if `port` is a valid port.

    **Example usage**

    >>> assert not valid_port(-1)
    >>> assert not valid_port('something not a port')
    >>> assert valid_port('80')
    >>> valid_port(65535)
    True
    """
    try:
        return 0 <= int(port) < 2**16
    except Exception:  # pylint:disable=broad-except
        return False


def valid_secret(secret: str | None, *, none_allowed: bool) -> bool:
    """
    Returns True if `secret` is a valid secret.

    A valid secret contains at least 8 alpha-numeric characters.

    **Example usage**

    >>> valid_secret('1234', none_allowed=False)
    False
    >>> valid_secret(None, none_allowed=True)
    True
    >>> valid_secret(None, none_allowed=False)
    False
    >>> valid_secret('my_password', none_allowed=False)
    True
    """
    if secret is None:
        return none_allowed
    try:
        return re.match(r'[A-Za-z0-9@#$%^&+=-_]{8,}', secret) is not None
    except Exception:  # pylint:disable=broad-except
        return False


def valid_uri(
    uri: str,
    *,
    check_404: bool,
    scheme_mandatory: bool = False,
    port_mandatory: bool = False,
    default_port: int = 80,
    excepted_errnos: tuple[int, ...] = (errno.ENOENT, errno.ECONNREFUSED, errno.ENETUNREACH),
    timeout: int | None = None
) -> bool:
    """
    Validate an URI.

    *Example usage**

    >>> valid_uri('http://docs.python.org/2/library/httplib.html', check_404=True)
    True
    >>> valid_uri('//docs.python.org/2/library/httplib.html', check_404=True)
    True
    >>> valid_uri('domain_not_exist_404_404/index.htmlw', check_404=True)
    False

    Set default value for port [time'd out request]:

    >>> valid_uri('http://google.com/pytoolbox', check_404=True, default_port=80, timeout=0.2)
    False

    Following the syntax ... in RFC 1808, ... input is presumed ... a path component:

    >>> valid_uri('docs.python.org/2/library/httplib.html', check_404=True)
    False

    This function does not use scheme of `uri` at all, so here is the proof:

    >>> valid_uri('gluster://docs.python.org/2/library/httplib.html', check_404=True)
    True

    Enforce the scheme or the port to being set:

    >>> valid_uri(
    ...     '//domain_not_exist_404_404/index.html:80', check_404=False, scheme_mandatory=True)
    False
    >>> valid_uri('//domain_not_exist_404_404/index.html:80', check_404=False, port_mandatory=True)
    False
    """
    url = urlparse(uri)
    if not url.netloc or scheme_mandatory and not url.scheme or port_mandatory and not url.port:
        return False
    if check_404:
        conn = http.client.HTTPConnection(url.netloc, url.port or default_port, timeout=timeout)
        try:
            conn.request('HEAD', url.path)
            return conn.getresponse().status != 404
        except socket.error as ex:
            # Resource does not exist
            if isinstance(ex, socket.timeout) or ex.errno in excepted_errnos:
                return False
            raise  # Re-raise exception if a different error occurred
        finally:
            conn.close()
    return True


def valid_uuid(value: Any, *, objectid_allowed: bool = False, none_allowed: bool = False) -> bool:
    """
    Returns True if `id` is a valid UUID / ObjectId.

    **Example usage**

    >>> valid_uuid(None)
    False
    >>> valid_uuid(None, none_allowed=True)
    True
    >>> valid_uuid('gaga-gogo-gaga-gogo')
    False
    >>> valid_uuid('gaga-gogo-gaga-gogo', objectid_allowed=True)
    False
    >>> valid_uuid(uuid.uuid4(), none_allowed=False)
    True
    >>> valid_uuid(uuid.uuid4().hex, none_allowed=False)
    True
    >>> valid_uuid(str(uuid.uuid4().hex), none_allowed=False)
    True
    >>> valid_uuid(ObjectId())
    False
    >>> valid_uuid(ObjectId(), objectid_allowed=True)
    True
    >>> valid_uuid(ObjectId().binary, objectid_allowed=True)
    True
    """
    if value is None:
        return none_allowed
    try:
        uuid.UUID('{{{0}}}'.format(value))  # pylint:disable=consider-using-f-string
    except ValueError:
        if not objectid_allowed:
            return False
        if ObjectId is None:
            raise RuntimeError('bson library not installed')  # pylint:disable=raise-missing-from
        try:
            ObjectId(value)
        except InvalidId:
            return False
    return True


def validate_list(the_list: list[Any], regexes: list[re.Pattern | str]) -> bool:
    """
    Validate every element of `the_list` with corresponding regular expression picked-in from
    `regexes`.
    """
    if len(the_list) != len(regexes):
        raise IndexError(
            f'{len(the_list)} elements to validate with '
            f'{len(regexes)} regular expressions')

    for counter, (regex, value) in enumerate(zip(regexes, the_list), 1):
        if not re.match(regex, str(value)):
            raise ValueError(
                f'N°{counter} is invalid:{os.linesep}'
                f'\telement: {value}{os.linesep}'
                f'\tregex:   {regex}')


__all__ = _all.diff(globals())
