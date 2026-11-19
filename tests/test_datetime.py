"""Tests for the datetime module."""

from __future__ import annotations

from datetime import datetime, time, timedelta

import pytest

from pytoolbox import datetime as dt_module


def test_datetime_to_epoch_utc_false() -> None:
    """datetime_to_epoch(utc=False) must return the local epoch, not the UTC one."""
    from time import mktime

    date = datetime(2010, 6, 10)
    expected = int(mktime(date.timetuple()))
    result = dt_module.datetime_to_epoch(date, utc=False)
    assert result == expected


def test_str_to_time_microseconds() -> None:
    """str_to_time('00:03:02.12') should produce 120000 microseconds, not 120."""
    result = dt_module.str_to_time('00:03:02.12')
    assert result == time(0, 3, 2, 120000)


def test_str_to_time_microseconds_small() -> None:
    """str_to_time() correctly parses time strings with small microseconds."""
    result = dt_module.str_to_time('01:00:00.001')
    assert result == time(1, 0, 0, 1000)


def test_datetime_now_fmt_none_returns_datetime() -> None:
    """datetime_now() with fmt=None returns a datetime object."""
    result = dt_module.datetime_now(fmt=None)
    assert isinstance(result, datetime)


def test_datetime_now_fmt_str_returns_str() -> None:
    """datetime_now() with fmt string returns a formatted string."""
    result = dt_module.datetime_now(fmt='%Y-%m-%d')
    assert isinstance(result, str)


def test_timedelta_to_time_basic() -> None:
    """Converts a timedelta to the equivalent time of day."""
    result = dt_module.timedelta_to_time(timedelta(hours=1, minutes=30, seconds=45))
    assert result == time(1, 30, 45)


def test_timedelta_to_time_zero() -> None:
    """Zero timedelta returns midnight."""
    assert dt_module.timedelta_to_time(timedelta(0)) == time(0, 0)


def test_timedelta_to_time_seconds_only() -> None:
    """Timedelta with only seconds converts correctly."""
    assert dt_module.timedelta_to_time(timedelta(seconds=3661)) == time(1, 1, 1)


def test_total_seconds_refuses_an_unsupported_type() -> None:
    """total_seconds() raises NotImplementedError naming a value of an unsupported type."""
    with pytest.raises(NotImplementedError, match=r'Unable to process \[1\]'):
        dt_module.total_seconds([1])  # type: ignore[arg-type]
