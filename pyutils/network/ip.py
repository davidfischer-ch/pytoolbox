# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                   OPTIMIZED AND CROSS PLATFORM SMPTE 2022-1 FEC LIBRARY IN C, JAVA, PYTHON, +TESTBENCH
#
#  Description    : SMPTE 2022-1 FEC Library
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2008-2013 smpte2022lib Team. All rights reserved.
#  Sponsoring     : Developed for a HES-SO CTI Ra&D project called GaVi
#                   Haute école du paysage, d'ingénierie et d'architecture @ Genève
#                   Telecommunications Laboratory
#
#**********************************************************************************************************************#
#
# This file is part of smpte2022lib.
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
# Retrieved from https://github.com/davidfischer-ch/smpte2022lib.git

from __future__ import absolute_import

import sys

if sys.version_info[0] > 2:
    from ipaddress import ip_address
else:
    from ipaddr import IPAddress as ip_address


def IPSocket(string):
    u"""
    This helper create a dictionary containing address and port from a parsed IP address string.
    Throws ValueError in case of failure (e.g. string is not a valid IP address).

    **Example usage**

    >>> IPSocket(u'gaga:gogo')
    Traceback (most recent call last):
        ...
    ValueError: gaga:gogo is not a valid IP socket.

    >>> from nose.tools import assert_equal
    >>> assert_equal(IPSocket(u'239.232.0.222:5004'), {u'ip': u'239.232.0.222', u'port': 5004})


    .. warning::

        TODO IPv6 ready : >>> IPSocket(u'[2001:0db8:0000:0000:0000:ff00:0042]:8329')
    """
    try:
        (ip, port) = string.rsplit(u':', 1)
        #ip = ip.translate(None, '[]')
        ip_address(ip)  # Seem not IPv6 ready
        port = int(port)
    except Exception:
        raise ValueError(u'{0} is not a valid IP socket.'.format(string))
    return {u'ip': ip, u'port': port}
