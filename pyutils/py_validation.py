# -*- coding: utf-8 -*-

#**************************************************************************************************#
#                               PYUTILS - SOME PYTHON UTILITY FUNCTIONS
#
#   Description : Toolbox for Python scripts
#   Authors     : David Fischer
#   Contact     : david.fischer.ch@gmail.com
#   Copyright   : 2013-2013 David Fischer. All rights reserved.
#**************************************************************************************************#
#
#  This file is part of pyutils.
#
#  This project is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with this project.
#  If not, see <http://www.gnu.org/licenses/>
#
#  Retrieved from git clone https://github.com/davidfischer-ch/pyutils.git

import errno, httplib, re, six, socket, uuid
from bson.objectid import InvalidId, ObjectId
from kitchen.text.converters import to_bytes
from urlparse import urlparse

if six.PY3:
    from ipaddress import ip_address
else:
    from ipaddr import IPAddress as ip_address


def valid_filename(filename):
    u"""
    Returns True if ``filename`` is a valid filename.

    **Example usage**:

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

    **Example usage**:

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

    **Example usage**:

    >>> valid_email(u'Tabby@croquetes')
    False
    >>> valid_email(u'Tabby@bernex.ch')
    True
    """
    try:
        return True if re.match(ur'[^@]+@[^@]+\.[^@]+', email) else False
    except:
        return False


def valid_port(port):
    u"""
    Returns True if ``port`` is a valid port.

    **Example usage**:

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

    **Example usage**:

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
              excepted_errnos=(errno.ENOENT, errno.ECONNREFUSED, errno.ENETUNREACH)):
    u"""

    *Example usage**:

    >>> valid_uri('http://docs.python.org/2/library/httplib.html', check_404=True)
    True
    >>> valid_uri('//docs.python.org/2/library/httplib.html', check_404=True)
    True
    >>> valid_uri('domain_not_exist_404_404/index.htmlw', check_404=True)
    False

    Set default value for port (using a crazy port number to ensure a 404):
    >>> valid_uri('//docs.python.org/2/library/httplib.html', check_404=True, default_port=88881)
    False

    Following the syntax ... in RFC 1808, ... input is presumed ... a path component:
    >>> valid_uri('docs.python.org/2/library/httplib.html', check_404=True)
    False

    This method does not use scheme of ``uri`` at all, so here is the proof:
    >>> valid_uri('gluster://docs.python.org/2/library/httplib.html', check_404=True)
    True

    Enforce the scheme or the port to being set:
    >>> valid_uri('//domain_not_exist_404_404/index.html:80', check_404=False, scheme_mandatory=True)
    False
    >>> valid_uri('//domain_not_exist_404_404/index.html:80', check_404=False, port_mandatory=True)
    False

    Only accept to map a 'No such file or directory' standard :mod:`errno` to False:
    >>> valid_uri('//docs.python.org/index.html', check_404=True, default_port=8080)
    False
    >>> valid_uri('//docs.python.org/index.html', check_404=True, excepted_errnos=(errno.ENOENT,), default_port=8080)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    error: ...
    """
    url = urlparse(uri)
    if not url.netloc or not url.path or scheme_mandatory and not url.scheme or port_mandatory and not url.port:
        return False
    if check_404:
        conn = httplib.HTTPConnection(url.netloc, url.port or default_port)
        try:
            conn.request('HEAD', url.path)
        except socket.error as e:
            # Resource does not exist
            if e.errno in excepted_errnos:
                return False
            raise  # Re-raise exception if a different error occurred
        response = conn.getresponse()
        conn.close()
        return response.status != 404
    return True


def valid_uuid(id, objectid_allowed=False, none_allowed=False):
    u"""
    Returns True if ``id`` is a valid UUID / ObjectId.

    **Example usage**:

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
    >>> valid_uuid(str(ObjectId().binary), objectid_allowed=True)
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
            ObjectId(str(id))
        except InvalidId:
            return False
    return True


def validate_list(the_list, regexes):
    u"""
    Validate every element of ``the_list`` with corresponding regular expression picked-in from ``regexes``.
    """
    if len(the_list) != len(regexes):
        raise IndexError(to_bytes(u'{0} elements to validate with {1} regular expressions'.format(len(the_list), len(regexes))))
    for i in range(len(regexes)):
        if not re.match(regexes[i], unicode(the_list[i])):
            raise ValueError(to_bytes(u'N°{0} is invalid:\n\telement: {1}\n\tregex:   {2}'.format(i+1, the_list[i], regexes[i])))
