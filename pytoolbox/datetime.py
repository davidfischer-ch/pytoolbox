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

import datetime, numbers, pytz
from calendar import timegm
from time import mktime
from .encoding import string_types


def datetime_now(format='%Y-%m-%d %H:%M:%S', append_utc=False, offset=None, tz=pytz.utc):
    u"""
    Return the current (timezone aware) date and time as UTC (tz=pytz.utc), local (tz=None) or related to a timezone.
    If format is not None, the date will be returned in a formatted string.

    :param format: Output date string formatting
    :type format: str
    :param append_utc: Append ' UTC' to date string
    :type append_utc: bool
    :param offset: Offset to add to current time
    :type offset: datetime.timedelta
    :param tz: The timezone (e.g. pytz.timezone(u'EST'))
    :type tz: tz

    **Example usage**

    Add an offset:

    >>> now = datetime_now(format=None)
    >>> future = datetime_now(offset=datetime.timedelta(hours=2, minutes=10), format=None)
    >>> print(future - now)  # doctest: +ELLIPSIS
    2:10:00...

    Append UTC to output date string:

    >>> assert(isinstance(datetime_now(), string_types))
    >>> assert(u' UTC' not in datetime_now(tz=pytz.utc, append_utc=False))
    >>> assert(u' UTC' not in datetime_now(tz=None, append_utc=True))
    >>> assert(u' UTC' not in datetime_now(tz=pytz.timezone(u'EST'), append_utc=True))
    >>> assert(u' UTC' in datetime_now(tz=pytz.utc, append_utc=True))

    Play with timezones:

    >> datetime_now(tz=pytz.timezone(u'Europe/Zurich'))
    u'2013-10-17 09:54:08'
    >> datetime_now(tz=pytz.timezone(u'US/Eastern'))
    u'2013-10-17 03:54:08'
    """
    now = datetime.datetime.now(tz)
    if offset:
        now += offset
    return (now.strftime(format) + (u' UTC' if tz == pytz.utc and append_utc else u'')) if format else now


def datetime2str(date_time, format=u'%Y-%m-%d %H:%M:%S', append_utc=False):
    return date_time.strftime(format) + (u' UTC' if append_utc else u'')


def str2datetime(date, format=u'%Y-%m-%d %H:%M:%S'):
    u"""
    Return the date string converted into an instance of datetime.

    **Example usage**

    >>> str2datetime(u'1985-01-06 05:02:00')
    datetime.datetime(1985, 1, 6, 5, 2)
    >>> str2datetime(u'this is not a date')
    Traceback (most recent call last):
        ...
    ValueError: time data 'this is not a date' does not match format '%Y-%m-%d %H:%M:%S'
    """
    return datetime.datetime.strptime(date, format)


def secs_to_time(value, defaults_to_zero=False):
    u"""
    Return an instance of time, taking value as the number of seconds + microseconds (e.g. 10.3 = 10s 3000us).

    **Example usage**

    >>> secs_to_time(83707.0035)
    datetime.time(23, 15, 7, 3500)
    >>> secs_to_time(None)
    >>> secs_to_time(None, defaults_to_zero=True)
    datetime.time(0, 0)
    """
    try:
        return (datetime.datetime.min + datetime.timedelta(seconds=float(value))).time()
    except (TypeError, ValueError):
        if defaults_to_zero and not value:
            return datetime.time(second=0)
        return None


def time_ratio(numerator, denominator, zero_div_result=1.0):
    u"""
    Return the ratio between two times.

    **Example usage**

    >>> print(time_ratio(u'0:30:00', u'01:30:00'))  # doctest: +ELLIPSIS
    0.33...
    >>> print(time_ratio(u'0:00:05', u'00:00:00'))  # doctest: +ELLIPSIS
    1.0
    >>> print(time_ratio(u'01:42:34', u'N/A'))
    Traceback (most recent call last):
        ...
    ValueError: could not convert string to float: N/A
    """
    try:
        ratio = total_seconds(numerator) / total_seconds(denominator)
        return 0.0 if ratio < 0.0 else 1.0 if ratio > 1.0 else ratio
    except ZeroDivisionError:
        return zero_div_result


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
    >>> total_seconds(datetime.datetime(2010, 6, 10, 0, 1, 30))
    90.0
    >>> total_seconds(datetime.datetime(2010, 6, 10, 14, 15, 23))
    51323.0
    >>> total_seconds(datetime.datetime(2010, 6, 10, 23, 59, 59))
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


def datetime2epoch(date_time, utc=True, factor=1):
    u"""
    Return the datetime/date converted into an Unix epoch.
    Default ``factor`` means that the result is in seconds.

    **Example usage**

    >>> datetime2epoch(datetime.datetime(1970, 1, 1), factor=1)
    0
    >>> datetime2epoch(datetime.datetime(2010, 6, 10))
    1276128000
    >>> datetime2epoch(datetime.datetime(2010, 6, 10), factor=1000)
    1276128000000
    >>> datetime2epoch(datetime.date(2010, 6, 10), factor=1000)
    1276128000000
    >>> datetime2epoch(datetime.date(1987, 6, 10), factor=1000)
    550281600000

    In Switzerland:

    >> datetime2epoch(datetime.datetime(1970, 1, 1), utc=False, factor=1)
    -3600
    >> datetime2epoch(datetime.date(1970, 1, 1), utc=False, factor=1)
    -3600
    """
    if utc:
        time_tuple = date_time.utctimetuple() if hasattr(date_time, 'utctimetuple') else date_time.timetuple()
        return int(timegm(time_tuple) * factor)
    return int(mktime(date_time.timetuple()) * factor)


def epoch2datetime(unix_epoch, tz=pytz.utc, factor=1):
    u"""
    Return the Unix epoch converted to a datetime. Default ``factor`` means that the ``unix_epoch`` is in seconds.

    **Example usage**

    >>> from nose.tools import assert_equal
    >>> epoch2datetime(0, factor=1)
    datetime.datetime(1970, 1, 1, 0, 0, tzinfo=<UTC>)
    >>> epoch2datetime(1276128000, factor=1)
    datetime.datetime(2010, 6, 10, 0, 0, tzinfo=<UTC>)
    >>> epoch2datetime(1276128000, tz=pytz.timezone(u'Europe/Zurich'), factor=1)
    datetime.datetime(2010, 6, 10, 2, 0, tzinfo=<DstTzInfo 'Europe/Zurich' CEST+2:00:00 DST>)
    >>> epoch2datetime(1276128000000, factor=1000)
    datetime.datetime(2010, 6, 10, 0, 0, tzinfo=<UTC>)
    >>> today = datetime.datetime(1985, 6, 1, 5, 2, 0, tzinfo=pytz.utc)
    >>> assert_equal(epoch2datetime(datetime2epoch(today, factor=1000), factor=1000), today)
    """
    return datetime.datetime.fromtimestamp(unix_epoch / factor, tz)
