# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                       PYUTILS - TOOLBOX FOR PYTHON SCRIPTS
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

from __future__ import absolute_import

import numbers
from datetime import datetime, timedelta
from time import mktime
from .encoding import string_types


def datetime_now(offset=None, format='%Y-%m-%d %H:%M:%S', append_utc=False):
    u"""
    Return the current UTC date and time. If format is not None, the date will be returned in a formatted string.

    :param offset: Offset added to datetime.utcnow() if set
    :type offset: datetime.timedelta
    :param format: Output date string formatting
    :type format: str
    :param append_utc: Append ' UTC' to date string
    :type append_utc: bool

    **Example usage**

    >>> now = datetime_now(format=None)
    >>> future = datetime_now(offset=timedelta(hours=2, minutes=10), format=None)
    >>> print(future - now)  # doctest: +ELLIPSIS
    2:10:00...
    >>> assert(isinstance(datetime_now(), string_types))
    >>> assert(u' UTC' not in datetime_now(append_utc=False))
    >>> assert(u' UTC' in datetime_now(append_utc=True))
    """
    now = datetime.utcnow()
    if offset:
        now += offset
    return (now.strftime(format) + (u' UTC' if append_utc else u'')) if format else now


def datetime2str(date_time, format=u'%Y-%m-%d %H:%M:%S', append_utc=False):
    return date_time.strftime(format) + (u' UTC' if append_utc else u'')


def str2datetime(date, format=u'%Y-%m-%d %H:%M:%S'):
    return datetime.strptime(date, format)


def total_seconds(time):
    u"""
    Return the time converted in seconds.

    **Example usage**

    >>> total_seconds(u'00:10:00')
    600.0
    >>> total_seconds(u'01:54:17')
    6857.0
    >>> print(round(total_seconds(u'16.40'), 3))
    16.4
    >>> total_seconds(143.2)
    143.2
    >>> total_seconds(datetime(2010, 6, 10, 0, 1, 30))
    90.0
    >>> total_seconds(datetime(2010, 6, 10, 14, 15, 23))
    51323.0
    >>> total_seconds(datetime(2010, 6, 10, 23, 59, 59))
    86399.0
    """
    try:
        if isinstance(time, string_types):
            hours, minutes, seconds = time.split(u':')
        elif isinstance(time, numbers.Number):
            return time
        else:
            hours, minutes, seconds = time.hour, time.minute, time.second
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    except ValueError:
        return float(time)


def datetime2epoch(date_time, factor=1):
    u"""
    Return the datetime/date converted into an Unix epoch. Default ``factor`` means that the result is in seconds.

    **Example usage**

    >>> datetime2epoch(datetime(1970, 1, 1, 1, 0), factor=1)
    0
    >>> datetime2epoch(datetime(2010, 6, 10))
    1276120800
    >>> datetime2epoch(datetime(2010, 6, 10), factor=1000)
    1276120800000
    """
    return int(mktime(date_time.timetuple()) * factor)


def epoch2datetime(unix_epoch, factor=1):
    u"""
    Return the Unix epoch converted to a datetime. Default ``factor`` means that the ``unix_epoch`` is in seconds.

    **Example usage**

    >>> from nose.tools import assert_equal
    >>> epoch2datetime(0, factor=1)
    datetime.datetime(1970, 1, 1, 1, 0)
    >>> epoch2datetime(1276120800, factor=1)
    datetime.datetime(2010, 6, 10, 0, 0)
    >>> epoch2datetime(1276120800000, factor=1000)
    datetime.datetime(2010, 6, 10, 0, 0)
    >>> today = datetime(1985, 6, 1, 5, 2, 0)
    >>> assert_equal(epoch2datetime(datetime2epoch(today, factor=1000), factor=1000), today)
    """
    return datetime.fromtimestamp(unix_epoch / factor)
