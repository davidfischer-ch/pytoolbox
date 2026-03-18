from __future__ import annotations

import datetime

from pytoolbox.django import templatetags


def test_duration_hours_minutes_seconds() -> None:
    """Full timedelta renders all three components."""
    result = templatetags.duration(datetime.timedelta(hours=2, minutes=5, seconds=30))
    assert '2' in result and 'hour' in result
    assert '5' in result and 'minute' in result
    assert '30' in result and 'second' in result


def test_duration_singular() -> None:
    """Singular forms used when each component equals 1."""
    result = templatetags.duration(datetime.timedelta(hours=1, minutes=1, seconds=1))
    assert 'hour' in result and 'hours' not in result
    assert 'minute' in result and 'minutes' not in result
    assert 'second' in result and 'seconds' not in result


def test_duration_zero() -> None:
    """Zero timedelta renders only the seconds component."""
    result = templatetags.duration(datetime.timedelta(0))
    assert '0' in result and 'second' in result


def test_duration_none() -> None:
    """None returns the invalid string marker."""
    assert templatetags.duration(None) == templatetags.string_if_invalid


def test_naturalbitrate() -> None:
    """Converts bps to human-readable bitrate, None returns invalid string."""
    assert '16.5 Mb/s' in templatetags.naturalbitrate(16487211.33)
    assert templatetags.naturalbitrate(None) == templatetags.string_if_invalid


def test_naturalfilesize() -> None:
    """Converts bytes to human-readable file size, None returns invalid string."""
    assert '15.7 MB' in templatetags.naturalfilesize(16487211.33)
    assert templatetags.naturalfilesize(None) == templatetags.string_if_invalid
