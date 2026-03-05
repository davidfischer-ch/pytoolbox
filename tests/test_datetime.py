from __future__ import annotations

import datetime

from pytoolbox import datetime as dt_module


def test_datetime_to_epoch_utc_false() -> None:
    """datetime_to_epoch(utc=False) must return the local epoch, not the UTC one."""
    from time import mktime
    date = datetime.datetime(2010, 6, 10)
    expected = int(mktime(date.timetuple()))
    result = dt_module.datetime_to_epoch(date, utc=False)
    assert result == expected


def test_str_to_time_microseconds() -> None:
    """str_to_time('00:03:02.12') should produce 120000 microseconds, not 120."""
    result = dt_module.str_to_time('00:03:02.12')
    assert result == datetime.time(0, 3, 2, 120000)


def test_str_to_time_microseconds_small() -> None:
    result = dt_module.str_to_time('01:00:00.001')
    assert result == datetime.time(1, 0, 0, 1000)


def test_datetime_now_fmt_none_returns_datetime() -> None:
    result = dt_module.datetime_now(fmt=None)
    assert isinstance(result, datetime.datetime)


def test_datetime_now_fmt_str_returns_str() -> None:
    result = dt_module.datetime_now(fmt='%Y-%m-%d')
    assert isinstance(result, str)
