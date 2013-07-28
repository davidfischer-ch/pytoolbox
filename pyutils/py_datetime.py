#!/usr/bin/env python
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

from datetime import datetime


def datetime_now(offset=None, format='%Y-%m-%d %H:%M:%S', append_utc=False):
    u"""
    Return the current UTC date and time.
    If format is not None, the date will be returned in a formatted string.

    :param offset: Offset added to datetime.utcnow() if set
    :type offset: datetime.timedelta
    :param format: Output date string formatting
    :type format: str
    :param append_utc: Append ' UTC' to date string
    :type append_utc: bool

    **Example usage**:

    >>> from six import string_types
    >>> from datetime import timedelta
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


def duration2secs(duration):
    u"""
    Returns the duration converted in seconds.

    **Example usage**:

    >>> duration2secs(u'00:10:00')
    600.0
    >>> duration2secs(u'01:54:17')
    6857.0
    >>> print(round(duration2secs(u'16.40'), 3))
    16.4
    """
    try:
        hours, minutes, seconds = duration.split(u':')
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    except ValueError:
        return float(duration)


def str2datetime(date, format=u'%Y-%m-%d %H:%M:%S'):
    return datetime.strptime(date, format)
