# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pytoolbox Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division, print_function, unicode_literals

import errno, httplib, re, socket, sys, uuid
from bson.objectid import InvalidId, ObjectId
from urlparse import urlparse
from .encoding import to_bytes

if sys.version_info[0] > 2:
    from ipaddress import ip_address
else:
    try:
        from ipaddr import IP as ip_address
    except ImportError:  # previously IPAddress ...
        from ipaddr import IPAddress as ip_address


if sys.version_info[0] > 2:
    class StrongTypedMixin(object):
        u"""
        Annotate arguments of the class __init__ with types and then you'll get a class with type checking.

        **Example usage**

        >>> class Settings(StrongTypedMixin):
        ...     def __init__(self, *, locale: str, broker: dict, debug: bool=True, timezone=None):
        ...        self.locale = locale
        ...        self.broker = broker
        ...        self.debug = debug
        ...        self.timezone = timezone
        ...
        >>> settings = Settings(locale='fr', broker={}, debug=False)
        >>> settings = Settings(locale='fr', broker={}, timezone='this argument is not type checked')
        >>> settings = Settings(locale=10, broker={})
        Traceback (most recent call last):
            ...
        AssertionError: Attribute locale must be set to an instance of <class 'str'>
        """
        def __setattr__(self, name, value):
            the_type = self.__init__.__annotations__.get(name)
            if the_type:
                assert isinstance(value, the_type), 'Attribute %s must be set to an instance of %s' % (name, the_type)
            super().__setattr__(name, value)


def valid_filename(filename):
    u"""
    Returns True if ``filename`` is a valid filename.

    **Example usage**

    >>> valid_filename(u'my_file_without_extension')
    False
    >>> valid_filename(u'my_file_with_extension.mp4')
    True
    """
    try:
        return True if re.match(ur'[^\.]+\.[^\.]+', filename) else False
    except:
        return False


def valid_ip(ip):
    u"""
    Returns True if ``ip`` is a valid IP address.

    **Example usage**

    >>> valid_ip(u'123.0.0.')
    False
    >>> valid_ip(u'239.232.0.222')
    True
    """
    try:
        ip_address(ip)
        return True
    except:
        return False


def valid_email(email):
    u"""
    Returns True if ``email`` is a valid e-mail address.

    **Example usage**

    >>> valid_email(u'Tabby@croquetes')
    False
    >>> valid_email(u'Tabby@bernex.ch')
    True
    """
    try:
        return True if re.match(ur'[^@]+@[^@]+\.[^@]+', email) else False
    except:
        return False


def valid_int(value):
    u"""
    Returns True if ``value`` is a valid integer (can be converted to an int).

    **Example usage**

    >>> valid_int(u'dimitri is not a valid integer')
    False
    >>> valid_int(u'-10')
    True
    """
    try:
        int(value)
        return True
    except ValueError:
        return False


def valid_port(port):
    u"""
    Returns True if ``port`` is a valid port.

    **Example usage**

    >>> assert(not valid_port(-1))
    >>> assert(not valid_port('something not a port'))
    >>> assert(valid_port(u'80'))
    >>> valid_port(65535)
    True
    """
    try:
        return 0 <= int(port) < 2**16
    except:
        return False


def valid_secret(secret, none_allowed):
    u"""
    Returns True if ``secret`` is a valid secret.

    A valid secret contains at least 8 alpha-numeric characters.

    **Example usage**

    >>> valid_secret(u'1234', False)
    False
    >>> valid_secret(None, True)
    True
    >>> valid_secret(None, False)
    False
    >>> valid_secret(u'my_password', False)
    True
    """
    if secret is None and none_allowed:
        return True
    try:
        return True if re.match(ur'[A-Za-z0-9@#$%^&+=-_]{8,}', secret) else False
    except:
        return False


def valid_uri(uri, check_404, scheme_mandatory=False, port_mandatory=False, default_port=80,
              excepted_errnos=(errno.ENOENT, errno.ECONNREFUSED, errno.ENETUNREACH), timeout=None):
    u"""

    *Example usage**

    >>> valid_uri('http://docs.python.org/2/library/httplib.html', check_404=True)
    True
    >>> valid_uri('//docs.python.org/2/library/httplib.html', check_404=True)
    True
    >>> valid_uri('domain_not_exist_404_404/index.htmlw', check_404=True)
    False

    Set default value for port (using a crazy port number to ensure a 404) [time'd out request]:

    >>> valid_uri('//docs.python.org/2/library/httplib.html', check_404=True, default_port=88881, timeout=0.2)
    False

    Following the syntax ... in RFC 1808, ... input is presumed ... a path component:

    >>> valid_uri('docs.python.org/2/library/httplib.html', check_404=True)
    False

    This function does not use scheme of ``uri`` at all, so here is the proof:

    >>> valid_uri('gluster://docs.python.org/2/library/httplib.html', check_404=True)
    True

    Enforce the scheme or the port to being set:

    >>> valid_uri('//domain_not_exist_404_404/index.html:80', check_404=False, scheme_mandatory=True)
    False
    >>> valid_uri('//domain_not_exist_404_404/index.html:80', check_404=False, port_mandatory=True)
    False

    Do not map any standard error :mod:`errno` to False (1. time-out, 2. saduhqwuhw does not exist):

    >>> valid_uri('//docs.python.org/index.html', check_404=True, default_port=8080, timeout=0.2, excepted_errnos=())
    False
    >>> valid_uri('//fr.wikipedia.org/saduhqwuhw', check_404=True, excepted_errnos=())
    False
    """
    url = urlparse(uri)
    if not url.netloc or scheme_mandatory and not url.scheme or port_mandatory and not url.port:
        return False
    if check_404:
        conn = httplib.HTTPConnection(url.netloc, url.port or default_port, timeout=timeout)
        try:
            conn.request('HEAD', url.path)
            response = conn.getresponse()
            return response.status != 404
        except socket.error as e:
            # Resource does not exist
            if isinstance(e, socket.timeout) or e.errno in excepted_errnos:
                return False
            raise  # Re-raise exception if a different error occurred
        finally:
            conn.close()
    return True


def valid_uuid(id, objectid_allowed=False, none_allowed=False):
    u"""
    Returns True if ``id`` is a valid UUID / ObjectId.

    **Example usage**

    >>> valid_uuid(None)
    False
    >>> valid_uuid(None, none_allowed=True)
    True
    >>> valid_uuid(u'gaga-gogo-gaga-gogo')
    False
    >>> valid_uuid(u'gaga-gogo-gaga-gogo', objectid_allowed=True)
    False
    >>> valid_uuid(uuid.uuid4(), none_allowed=False)
    True
    >>> valid_uuid(uuid.uuid4().hex, none_allowed=False)
    True
    >>> valid_uuid(unicode(uuid.uuid4().hex), none_allowed=False)
    True
    >>> valid_uuid(ObjectId())
    False
    >>> valid_uuid(ObjectId(), objectid_allowed=True)
    True
    >>> valid_uuid(ObjectId().binary, objectid_allowed=True)
    True
    """
    if id is None and none_allowed:
        return True
    try:
        uuid.UUID(u'{{{0}}}'.format(id))
    except ValueError:
        if not objectid_allowed:
            return False
        try:
            ObjectId(id)
        except InvalidId:
            return False
    return True


def validate_list(the_list, regexes):
    u"""Validate every element of ``the_list`` with corresponding regular expression picked-in from ``regexes``."""
    if len(the_list) != len(regexes):
        raise IndexError(to_bytes(u'{0} elements to validate with {1} regular expressions'.format(
                         len(the_list), len(regexes))))
    for i in xrange(len(regexes)):
        if not re.match(regexes[i], unicode(the_list[i])):
            raise ValueError(to_bytes(u'N°{0} is invalid:\n\telement: {1}\n\tregex:   {2}'.format(
                             i+1, the_list[i], regexes[i])))
