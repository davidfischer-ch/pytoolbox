from __future__ import annotations

from typing import Annotated, Any, Literal, TypeAlias, overload
from calendar import timegm
from time import mktime
import datetime

import pytz

from . import module

_all = module.All(globals())

TimeValue: TypeAlias = datetime.datetime | datetime.timedelta | float | int | str


@overload
def datetime_now(
    fmt: Literal[None],
    *,
    append_utc: bool = False,
    offset: datetime.timedelta | None = None,
    tz: Any = pytz.utc
) -> str:
    ...


@overload
def datetime_now(
    fmt: str = ...,
    *,
    append_utc: bool = False,
    offset: datetime.timedelta | None = None,
    tz: Any = pytz.utc
) -> datetime.datetime:
    ...


def datetime_now(
    fmt: Annotated[str | None, 'Output date string formatting (optional)'] = '%Y-%m-%d %H:%M:%S',
    *,
    append_utc: Annotated[bool, "Append ' UTC' to date string"] = False,
    offset: Annotated[datetime.timedelta | None, 'Offset to add to current time'] = None,
    tz: Annotated[Any, "The timezone (e.g. ``pytz.timezone('EST')``)"] = pytz.utc
):
    """
    Return the current (timezone aware) date and time as UTC, local (tz=None) or related to a
    timezone. If `fmt` is not None, the date will be returned in a formatted string.

    **Example usage**

    Add an offset:

    >>> now = datetime_now(fmt=None)
    >>> future = datetime_now(offset=datetime.timedelta(hours=2, minutes=10), fmt=None)
    >>> result = (future - now)
    >>> type(result)
    <class 'datetime.timedelta'>
    >>> print(result)
    2:10:00.00...

    Append UTC to output date string:

    >>> type(datetime_now())
    <class 'str'>
    >>> assert ' UTC' not in datetime_now(tz=pytz.utc, append_utc=False)
    >>> assert ' UTC' not in datetime_now(tz=None, append_utc=True)
    >>> assert ' UTC' not in datetime_now(tz=pytz.timezone('EST'), append_utc=True)
    >>> assert ' UTC' in datetime_now(tz=pytz.utc, append_utc=True)

    Play with timezones::

        >> datetime_now(tz=pytz.timezone('Europe/Zurich'))
        '2013-10-17 09:54:08'
        >> datetime_now(tz=pytz.timezone('US/Eastern'))
        '2013-10-17 03:54:08'
    """
    now = datetime.datetime.now(tz)
    if offset is not None:
        now += offset
    if fmt is None:
        return now
    return now.strftime(fmt) + (' UTC' if tz == pytz.utc and append_utc else '')


def datetime_to_str(
    date_time: datetime.datetime,
    *,
    fmt: str = '%Y-%m-%d %H:%M:%S',
    append_utc: bool = False
) -> str:
    return date_time.strftime(fmt) + (' UTC' if append_utc else '')


@overload
def str_to_datetime(date: str, *, fmt: str = ..., fail: Literal[True] = True) -> datetime.datetime:
    ...


@overload
def str_to_datetime(date: str, *, fmt: str = ..., fail: Literal[False]) -> datetime.datetime | None:
    ...


def str_to_datetime(date, *, fmt='%Y-%m-%d %H:%M:%S', fail=True):
    """
    Return the `date` string converted into an instance of :class:`datetime.datetime`.
    Handle 24h+ hour format like 2015:06:28 24:05:00 equal to the 28th June 2015 at
    midnight and 5 minutes.

    **Example usage**

    >>> str_to_datetime('1985-01-06 05:02:00')
    datetime.datetime(1985, 1, 6, 5, 2)
    >>> str_to_datetime('this is not a date', fail=False) is None
    True
    >>> str_to_datetime('this is not a date')
    Traceback (most recent call last):
        ...
    ValueError: time data 'this is not a date' does not match format '%Y-%m-%d %H:%M:%S'
    """
    try:
        return datetime.datetime.strptime(date.replace(': ', ':0').replace(' 24:', ' 00:'), fmt)
    except ValueError:
        if fail and date != '0000:00:00 00:00:00':
            raise
    return None


@overload  # type: ignore[misc]
def multiply_time(
    value: TimeValue,
    factor: float,
    *,
    as_delta: Literal[False] = False
) -> datetime.time:
    ...


@overload
def multiply_time(
    value: TimeValue,
    factor: float,
    *,
    as_delta: Literal[True]
) -> datetime.timedelta:
    ...


def multiply_time(value: TimeValue, factor, *, as_delta=False):
    """
    Return an instance of :class:`datetime.time`/:class:`datetime.timedelta`
    corresponding to `value` multiplied by a `factor`.

    **Example usage**

    >>> multiply_time('00:10:00', 0.5)
    datetime.time(0, 5)
    >>> multiply_time(datetime.timedelta(seconds=60), 3)
    datetime.time(0, 3)
    >>> multiply_time(120, 0.1)
    datetime.time(0, 0, 12)
    >>> res = multiply_time(datetime.timedelta(seconds=152, microseconds=500000), 1, as_delta=True)
    >>> type(res)
    <class 'datetime.timedelta'>
    >>> print(res)
    0:02:32.500000
    """
    return secs_to_time(total_seconds(value) * factor, as_delta=as_delta)


@overload  # type: ignore[misc]
def parts_to_time(
    hours: int,
    minutes: int,
    seconds: int,
    microseconds: int,
    *,
    as_delta: Literal[False] = False
) -> datetime.time:
    ...


@overload
def parts_to_time(
    hours: int | float,
    minutes: int | float,
    seconds: int | float,
    microseconds: int | float,
    *,
    as_delta: Literal[True]
) -> datetime.timedelta:
    ...


def parts_to_time(hours, minutes, seconds, microseconds, *, as_delta=False):
    """
    Return an instance of :class:`datetime.time`/:class:`datetime.timedelta` out of the parts.

    **Example usage**

    >>> parts_to_time(23, 15, 7, 3500)
    datetime.time(23, 15, 7, 3500)
    >>> result = parts_to_time(23, 15, 7, 3500, as_delta=True)
    >>> type(result)
    <class 'datetime.timedelta'>
    >>> print(result)
    23:15:07.003500
    """
    if as_delta:
        return datetime.timedelta(
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            microseconds=microseconds)
    return datetime.time(hours, minutes, seconds, microseconds)


@overload  # type: ignore[misc]
def secs_to_time(value: float | int, *, as_delta: Literal[False] = False) -> datetime.time:
    ...


@overload
def secs_to_time(value: float | int, *, as_delta: Literal[True]) -> datetime.timedelta:
    ...


def secs_to_time(value, *, as_delta=False):
    """
    Return an instance of :class:`datetime.time`/:class:`datetime.timedelta`, taking `value` as the
    number of seconds + microseconds (e.g. 10.3 = 10s 3000us).

    **Example usage**

    >>> secs_to_time(83707.0035)
    datetime.time(23, 15, 7, 3500)
    >>> result = secs_to_time(83707.0035, as_delta=True)
    >>> type(result)
    <class 'datetime.timedelta'>
    >>> print(result)
    23:15:07.003500
    >>> secs_to_time(0)
    datetime.time(0, 0)
    >>> secs_to_time(0, as_delta=True)
    datetime.timedelta(0)
    """
    delta = datetime.timedelta(seconds=float(value))  # type: ignore[arg-type]
    return delta if as_delta else (datetime.datetime.min + delta).time()


@overload
def str_to_time(  # type: ignore[misc]
    value: str,
    *,
    defaults_to_zero: Literal[True],
    as_delta: Literal[False] = False
) -> datetime.time:
    ...


@overload  # type: ignore[misc]
def str_to_time(
    value: str,
    *,
    defaults_to_zero: Literal[True],
    as_delta: Literal[True]
) -> datetime.timedelta:
    ...


@overload  # type: ignore[misc]
def str_to_time(
    value: str,
    *,
    defaults_to_zero: Literal[False] = False,
    as_delta: Literal[False] = False
) -> datetime.time | None:
    ...


@overload  # type: ignore[misc]
def str_to_time(
    value: str,
    *,
    defaults_to_zero: Literal[False] = False,
    as_delta: Literal[True]
) -> datetime.timedelta | None:
    ...


def str_to_time(value, *, defaults_to_zero=False, as_delta=False):
    """
    Return the string of format 'hh:mm:ss' into an instance of time.

    **Example usage**

    >>> str_to_time('08:23:57')
    datetime.time(8, 23, 57)
    >>> str_to_time('00:03:02.12')
    datetime.time(0, 3, 2, 120)
    >>> result = str_to_time('08:23:57', as_delta=True)
    >>> type(result)
    <class 'datetime.timedelta'>
    >>> str(result)
    '8:23:57'
    >>> result = str_to_time('00:03:02.12', as_delta=True)
    >>> type(result)
    <class 'datetime.timedelta'>
    >>> str(result)
    '0:03:02.120000'
    """
    try:
        hours, minutes, seconds_float = value.split(':')
        hours, minutes, seconds_float = int(hours), int(minutes), float(seconds_float)
        if as_delta:
            return datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds_float)
        seconds = int(seconds_float)
        return datetime.time(hours, minutes, seconds, int(1000 * (seconds_float - seconds)))
    except (TypeError, ValueError):
        if defaults_to_zero and not value:
            return datetime.timedelta(seconds=0) if as_delta else datetime.time(second=0)
        return None


def time_ratio(
    numerator: TimeValue,
    denominator: TimeValue,
    *,
    zero_div_result: float = 1.0
) -> float:
    """
    Return the ratio between two times.

    **Example usage**

    >>> import pytest
    >>> time_ratio('0:30:00', '01:30:00')
    0.33...
    >>> time_ratio('0:00:05', '00:00:00')
    1.0
    >>> with pytest.raises(ValueError):
    ...     time_ratio('01:42:34', 'N/A')
    """
    try:
        ratio = total_seconds(numerator) / total_seconds(denominator)
        return 0.0 if ratio < 0.0 else 1.0 if ratio > 1.0 else ratio
    except ZeroDivisionError:
        return zero_div_result


def total_seconds(time: TimeValue) -> float:
    """
    Return the `time` converted in seconds.

    **Example usage**

    >>> total_seconds('00:10:00')
    600.0
    >>> total_seconds('01:54:17')
    6857.0
    >>> round(total_seconds('16.40'), 3)
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
    if isinstance(time, datetime.datetime):
        return time.hour * 3600 + time.minute * 60 + float(time.second)
    if isinstance(time, datetime.timedelta):
        return time.total_seconds()
    if isinstance(time, float | int):
        return float(time)
    if isinstance(time, str):
        try:
            hours, minutes, seconds = time.split(':')
        except ValueError:
            return float(time)
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    raise NotImplementedError(f'Unable to process {time:!r}')


def datetime_to_epoch(
    date_time: datetime.datetime | datetime.date,
    *,
    utc: bool = True,
    factor: int = 1
) -> int:
    """
    Return the :class:`datetime.datetime`/:class:`datetime.date` converted into an Unix epoch.
    Default `factor` means that the result is in seconds.

    **Example usage**

    >>> datetime_to_epoch(datetime.datetime(1970, 1, 1))
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

        >> datetime_to_epoch(datetime.datetime(1970, 1, 1), utc=False)
        -3600
        >> datetime_to_epoch(datetime.date(1970, 1, 1), utc=False)
        -3600
    """
    if not utc:
        int(mktime(date_time.timetuple()) * factor)
    if hasattr(date_time, 'utctimetuple'):
        return int(timegm(date_time.utctimetuple()) * factor)
    return int(timegm(date_time.timetuple()) * factor)


def epoch_to_datetime(unix_epoch: int, *, tz=pytz.utc, factor: int = 1) -> datetime.datetime:
    """
    Return the Unix epoch converted to a :class:`datetime.datetime`.
    Default `factor` means that the `unix_epoch` is in seconds.

    **Example usage**

    >>> epoch_to_datetime(0)
    datetime.datetime(1970, 1, 1, 0, 0, tzinfo=<UTC>)
    >>> epoch_to_datetime(1276128000)
    datetime.datetime(2010, 6, 10, 0, 0, tzinfo=<UTC>)
    >>> epoch_to_datetime(1276128000, tz=pytz.timezone('Europe/Zurich'))
    datetime.datetime(2010, 6, 10, 2, 0, tzinfo=<DstTzInfo 'Europe/Zurich' CEST+2:00:00 DST>)
    >>> epoch_to_datetime(1276128000000, factor=1000)
    datetime.datetime(2010, 6, 10, 0, 0, tzinfo=<UTC>)
    >>> today = datetime.datetime(1985, 6, 1, 5, 2, 0, tzinfo=pytz.utc)
    >>> epoch_to_datetime(datetime_to_epoch(today, factor=1000), factor=1000) == today
    True
    """
    return datetime.datetime.fromtimestamp(unix_epoch / factor, tz)


__all__ = _all.diff(globals())
