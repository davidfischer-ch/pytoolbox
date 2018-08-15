# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import datetime, numbers
from calendar import timegm
from time import mktime

import pytz

from . import module
from .encoding import string_types

_all = module.All(globals())


def datetime_now(format='%Y-%m-%d %H:%M:%S', append_utc=False, offset=None, tz=pytz.utc):  # noqa
    """
    Return the current (timezone aware) date and time as UTC, local (tz=None) or related to a timezone. If `format` is
    not None, the date will be returned in a formatted string.

    :param format: Output date string formatting
    :type format: str
    :param append_utc: Append ' UTC' to date string
    :type append_utc: bool
    :param offset: Offset to add to current time
    :type offset: datetime.timedelta
    :param tz: The timezone (e.g. ``pytz.timezone('EST')``)
    :type tz: tz

    **Example usage**

    Add an offset:

    >>> now = datetime_now(format=None)
    >>> future = datetime_now(offset=datetime.timedelta(hours=2, minutes=10), format=None)
    >>> print(future - now)  # doctest: +ELLIPSIS
    2:10:00...

    Append UTC to output date string:

    >>> assert(isinstance(datetime_now(), string_types))
    >>> assert(' UTC' not in datetime_now(tz=pytz.utc, append_utc=False))
    >>> assert(' UTC' not in datetime_now(tz=None, append_utc=True))
    >>> assert(' UTC' not in datetime_now(tz=pytz.timezone('EST'), append_utc=True))
    >>> assert(' UTC' in datetime_now(tz=pytz.utc, append_utc=True))

    Play with timezones::

        >> datetime_now(tz=pytz.timezone('Europe/Zurich'))
        '2013-10-17 09:54:08'
        >> datetime_now(tz=pytz.timezone('US/Eastern'))
        '2013-10-17 03:54:08'
    """
    now = datetime.datetime.now(tz)
    if offset is not None:
        now += offset
    return (now.strftime(format) + (' UTC' if tz == pytz.utc and append_utc else '')) if format else now


def datetime_to_str(date_time, format='%Y-%m-%d %H:%M:%S', append_utc=False):  # pylint:disable=redefined-builtin
    return date_time.strftime(format) + (' UTC' if append_utc else '')


def str_to_datetime(date, format='%Y-%m-%d %H:%M:%S', fail=True):  # pylint:disable=redefined-builtin
    """
    Return the `date` string converted into an instance of :class:`datetime.datetime`.
    Handle 24h+ hour format like 2015:06:28 24:05:00 equal to the 28th June 2015 at midnight and 5 minutes.

    **Example usage**

    >>> str_to_datetime('1985-01-06 05:02:00')
    datetime.datetime(1985, 1, 6, 5, 2)
    >>> str_to_datetime('this is not a date')
    Traceback (most recent call last):
        ...
    ValueError: time data 'this is not a date' does not match format '%Y-%m-%d %H:%M:%S'
    """
    try:
        return datetime.datetime.strptime(date.replace(': ', ':0').replace(' 24:', ' 00:'), format)
    except ValueError:
        if fail and date != '0000:00:00 00:00:00':
            raise


def multiply_time(value, factor, as_delta=False):
    """
    Return an instance of :class:`datetime.time`/:class:`datetime.timedelta` corresponding to `value` multiplied by a
    `factor`.

    **Example usage**

    >>> multiply_time('00:10:00', 0.5)
    datetime.time(0, 5)
    >>> multiply_time(datetime.timedelta(seconds=60), 3)
    datetime.time(0, 3)
    >>> multiply_time(120, 0.1)
    datetime.time(0, 0, 12)
    >>> multiply_time(datetime.timedelta(seconds=152, microseconds=500000), 1, as_delta=True)
    datetime.timedelta(0, 152, 500000)
    """
    return secs_to_time(total_seconds(value) * factor, as_delta=as_delta)


def parts_to_time(hours, minutes, seconds, microseconds, as_delta=False):
    """
    Return an instance of :class:`datetime.time`/:class:`datetime.timedelta` out of the parts.

    **Example usage**

    >>> parts_to_time(23, 15, 7, 3500)
    datetime.time(23, 15, 7, 3500)
    >>> parts_to_time(23, 15, 7, 3500, as_delta=True)
    datetime.timedelta(0, 83707, 3500)
    """
    if as_delta:
        return datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds)
    return datetime.time(hours, minutes, seconds, microseconds)


def secs_to_time(value, defaults_to_zero=False, as_delta=False):
    """
    Return an instance of :class:`datetime.time`/:class:`datetime.timedelta`, taking `value` as the number of seconds +
    microseconds (e.g. 10.3 = 10s 3000us).

    **Example usage**

    >>> secs_to_time(83707.0035)
    datetime.time(23, 15, 7, 3500)
    >>> secs_to_time(None)
    >>> secs_to_time(None, defaults_to_zero=True)
    datetime.time(0, 0)
    >>> secs_to_time(83707.0035, as_delta=True)
    datetime.timedelta(0, 83707, 3500)
    >>> secs_to_time(None, as_delta=True)
    >>> secs_to_time(None, defaults_to_zero=True, as_delta=True)
    datetime.timedelta(0)
    """
    try:
        delta = datetime.timedelta(seconds=float(value))
        return delta if as_delta else (datetime.datetime.min + delta).time()
    except (ValueError, TypeError):
        if defaults_to_zero and not value:
            return datetime.timedelta(seconds=0) if as_delta else datetime.time(second=0)
        return None


def str_to_time(value, defaults_to_zero=False, as_delta=False):
    """
    Return the string of format 'hh:mm:ss' into an instance of time.

    **Example usage**

    >>> str_to_time('08:23:57')
    datetime.time(8, 23, 57)
    >>> str_to_time('00:03:02.12')
    datetime.time(0, 3, 2, 120)
    >>> str_to_time(None)
    >>> str_to_time(None, defaults_to_zero=True)
    datetime.time(0, 0)
    >>> str_to_time('08:23:57', as_delta=True)
    datetime.timedelta(0, 30237)
    >>> str_to_time('00:03:02.12', as_delta=True)
    datetime.timedelta(0, 182, 120000)
    >>> str_to_time(None, as_delta=True)
    >>> str_to_time(None, defaults_to_zero=True, as_delta=True)
    datetime.timedelta(0)
    """
    try:
        hours, minutes, seconds_float = value.split(':')
        hours, minutes, seconds_float = int(hours), int(minutes), float(seconds_float)
        if as_delta:
            return datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds_float)
        seconds = int(seconds_float)
        return datetime.time(hours, minutes, seconds, int(1000 * (seconds_float - seconds)))
    except (AttributeError, TypeError, ValueError):
        if defaults_to_zero and not value:
            return datetime.timedelta(seconds=0) if as_delta else datetime.time(second=0)
        return None


def time_ratio(numerator, denominator, zero_div_result=1.0):
    """
    Return the ratio between two times.

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> print(time_ratio('0:30:00', '01:30:00'))  # doctest: +ELLIPSIS
    0.33...
    >>> print(time_ratio('0:00:05', '00:00:00'))  # doctest: +ELLIPSIS
    1.0
    >>> asserts.raises(ValueError, time_ratio, '01:42:34', 'N/A')
    """
    try:
        ratio = total_seconds(numerator) / total_seconds(denominator)
        return 0.0 if ratio < 0.0 else 1.0 if ratio > 1.0 else ratio
    except ZeroDivisionError:
        return zero_div_result


def total_seconds(time):
    """
    Return the `time` converted in seconds.

    **Example usage**

    >>> total_seconds('00:10:00')
    600.0
    >>> total_seconds('01:54:17')
    6857.0
    >>> print(round(total_seconds('16.40'), 3))
    16.4
    >>> total_seconds(143.2)
    143.2
    >>> total_seconds(datetime.timedelta(seconds=152, microseconds=500000))
    152.5
    >>> total_seconds(datetime.datetime(2010, 6, 10, 0, 1, 30))
    90.0
    >>> total_seconds(datetime.datetime(2010, 6, 10, 14, 15, 23))
    51323.0
    >>> total_seconds(datetime.datetime(2010, 6, 10, 23, 59, 59))
    86399.0
    """
    try:
        if isinstance(time, datetime.timedelta):
            return time.total_seconds()
        elif isinstance(time, numbers.Number):
            return time
        elif isinstance(time, string_types):
            hours, minutes, seconds = time.split(':')
        else:
            hours, minutes, seconds = time.hour, time.minute, time.second
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    except ValueError:
        return float(time)


def datetime_to_epoch(date_time, utc=True, factor=1):
    """
    Return the :class:`datetime.datetime`/:class:`datetime.date` converted into an Unix epoch. Default `factor` means
    that the result is in seconds.

    **Example usage**

    >>> datetime_to_epoch(datetime.datetime(1970, 1, 1), factor=1)
    0
    >>> datetime_to_epoch(datetime.datetime(2010, 6, 10))
    1276128000
    >>> datetime_to_epoch(datetime.datetime(2010, 6, 10), factor=1000)
    1276128000000
    >>> datetime_to_epoch(datetime.date(2010, 6, 10), factor=1000)
    1276128000000
    >>> datetime_to_epoch(datetime.date(1987, 6, 10), factor=1000)
    550281600000

    In Switzerland::

        >> datetime_to_epoch(datetime.datetime(1970, 1, 1), utc=False, factor=1)
        -3600
        >> datetime_to_epoch(datetime.date(1970, 1, 1), utc=False, factor=1)
        -3600
    """
    if utc:
        time_tuple = date_time.utctimetuple() if hasattr(date_time, 'utctimetuple') else date_time.timetuple()
        return int(timegm(time_tuple) * factor)
    return int(mktime(date_time.timetuple()) * factor)


def epoch_to_datetime(unix_epoch, tz=pytz.utc, factor=1):
    """
    Return the Unix epoch converted to a :class:`datetime.datetime`. Default `factor` means that the `unix_epoch` is in
    seconds.

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> epoch_to_datetime(0, factor=1)
    datetime.datetime(1970, 1, 1, 0, 0, tzinfo=<UTC>)
    >>> epoch_to_datetime(1276128000, factor=1)
    datetime.datetime(2010, 6, 10, 0, 0, tzinfo=<UTC>)
    >>> epoch_to_datetime(1276128000, tz=pytz.timezone('Europe/Zurich'), factor=1)
    datetime.datetime(2010, 6, 10, 2, 0, tzinfo=<DstTzInfo 'Europe/Zurich' CEST+2:00:00 DST>)
    >>> epoch_to_datetime(1276128000000, factor=1000)
    datetime.datetime(2010, 6, 10, 0, 0, tzinfo=<UTC>)
    >>> today = datetime.datetime(1985, 6, 1, 5, 2, 0, tzinfo=pytz.utc)
    >>> asserts.equal(epoch_to_datetime(datetime_to_epoch(today, factor=1000), factor=1000), today)
    """
    return datetime.datetime.fromtimestamp(unix_epoch / factor, tz)


__all__ = _all.diff(globals())
