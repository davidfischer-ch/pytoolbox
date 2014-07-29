# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2014 David Fischer. All rights reserved.
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

import sys

if sys.version_info[0] > 2:
    from ipaddress import ip_address
else:
    try:
        from ipaddr import IP as ip_address
    except ImportError:  # previously IPAddress ...
        from ipaddr import IPAddress as ip_address


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
    >>> from nose.tools import eq_
    >>> eq_(IPSocket('239.232.0.222:5004'), {'ip': '239.232.0.222', 'port': 5004})

    .. warning::

        TODO IPv6 ready : >>> IPSocket('[2001:0db8:0000:0000:0000:ff00:0042]:8329')
    """
    try:
        (ip, port) = string.rsplit(':', 1)
        #ip = ip.translate(None, '[]')
        ip_address(ip)  # Seem not IPv6 ready
        port = int(port)
    except Exception:
        raise ValueError('{0} is not a valid IP socket.'.format(string))
    return {'ip': ip, 'port': port}
